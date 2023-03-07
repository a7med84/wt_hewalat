# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import ValidationError, UserError
import datetime
import pandas as pd
from ..utils.crypto import decrypt


BANK_VIEW_IDS = {
    "الراجحي": 'wt_hewalat_rajhi_transfer_view_tree',
    "الأهلي": 'wt_hewalat_ahly_transfer_view_tree',
    "الانماء": 'wt_hewalat_inma_transfer_view_tree',
    "البلاد": 'wt_hewalat_belad_transfer_view_tree',
    "ساب": 'wt_hewalat_sab_transfer_view_tree',
}

class BanktransferWizard(models.TransientModel):
    _name = "wt.hewalat.banktransfer.wizard"
    _description = "Banktransfer wizard"

    details = fields.Char()
    reference = fields.Char(string="Reference Number")
    date = fields.Date(string='Date')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    account_id = fields.Integer(readonly=True)
    bank_account = fields.Char(string="Account", readonly=True)
    bank = fields.Char(string="Bank", readonly=True)
    has_transfers = fields.Boolean(readonly=True)
    transfers_min_date = fields.Date(readonly=True)
    transfers_max_date = fields.Date(readonly=True)
    user_is_manager = fields.Boolean(readonly=True)
    
        
    def action_serch(self):
        data = self.read(['details', 'reference', 'date', 'date_from', 'date_to'])[0]
        filters = [k for k,v in data.items() if v]
        if len(filters) < 2:
           raise ValidationError(_('No inputs entered'))
        
        if 'details' in filters:
            if len(data['details']) < 4:
               raise ValidationError(_('Details Field cannot be less than 4 letters'))
        if 'reference' in filters:
            if len(data['reference']) < 4:
               raise ValidationError(_('Reference Field cannot be less than 4 letters'))

        cols = [col for col in filters if 'date' not in col] + ['credit', 'date']
        cols_str = ','. join(cols)

        bank_id = self.read(['account_id'])[0]['account_id']
        query = f'(SELECT {cols_str} FROM wt_hewalat_bank_transfer where bank_account_id = {bank_id})'
        cr = self._cr
        cr.execute(query)
        result = cr.fetchall()
        df = pd.DataFrame(result, columns=cols).set_index('id')
        df = df.applymap(decrypt)

        df.credit = df.credit.astype(float)
        if not self.user_is_manager:
            df = df.query("credit > 0")
        

        df.date = pd.to_datetime(df.date, format='%d/%m/%Y')
        if 'date' in filters:
            date_param = date_str(data['date'])
            df = df.query("date == @date_param")

        if 'date_from' in filters:
            date_param = date_str(data['date_from'])
            df = df.query("date >= @date_param")

        if 'date_to' in filters:
            date_param = date_str(data['date_to'])
            df = df.query("date <= @date_param")
        
        if 'details' in filters:
            df = df.loc[df.details.str.contains(data['details'], case=False, na=False)]

        if 'reference' in filters:
            df = df.loc[df.reference.str.contains(data['reference'], case=False, na=False)]

        action = self.env.ref('wt_hewalat.wt_hewalat_bank_transfers_action').read()[0]
        action.update({
            'domain': [('id', 'in', df.index.tolist())],
            'views': [(_get_view_id(self, bank_id), 'tree')],
            'help': """<p class="o_view_nocontent_neutral_face">{}</p>""".format(_('No Results')),
        })
        return action


def date_str(date):
    try:
        date_param = datetime.datetime.strftime(date, "%Y/%m/%d")
    except ValueError:
        date_param = datetime.datetime.strftime(date, "%d/%m/%Y")
    return date_param


def _get_view_id(obj, bank_id):
    account = obj.env['wt.hewalat.bank.account'].browse([bank_id])
    _id = BANK_VIEW_IDS.get(account.bank, False)
    if not _id:
        # if unknow bank raise error
        raise UserError(_('Searching transfers is not implemented for bank ' + account.bank))
    return obj.env.ref(f'wt_hewalat.{_id}').read()[0]['id']

