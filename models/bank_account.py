# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

class BankAccount(models.Model):
    _name = 'wt.hewalat.bank.account'
    _description = 'Bank Account'
    _order ="id"

    name = fields.Char(string='Name')
    bank = fields.Char(string='Bank')
    transfer_ids = fields.One2many('wt.hewalat.bank.transfer', 'bank_account_id', string='Transfers')
    has_transfers = fields.Boolean(compute="_has_transfers", readonly=True)
    transfers_min_date = fields.Date(compute="_transfers_min_date", readonly=True)
    transfers_max_date = fields.Date(compute="_transfers_max_date", readonly=True)
    user_is_manager = fields.Boolean(compute="_user_is_manager", readonly=True)

    
    def name_get(self):
        result = []         
        for rec in self:
            result.append((rec.id, f'{rec.name} - بنك {rec.bank}'))  
        return result

    
    @api.depends('transfer_ids')
    def _has_transfers(self):
        for rec in self:
            rec.has_transfers = any(rec.transfer_ids)

    @api.depends('transfer_ids.date')
    def _transfers_min_date(self):
        for rec in self:
            _has_recs = any(rec.transfer_ids)
            rec.transfers_min_date = min(rec.transfer_ids.mapped('date_comp')) if _has_recs else False


    @api.depends('transfer_ids.date')
    def _transfers_max_date(self):
        for rec in self:
            _has_recs = any(rec.transfer_ids)
            rec.transfers_max_date = max(rec.transfer_ids.mapped('date_comp')) if _has_recs else False


    def _user_is_manager(self):
        for rec in self:
            rec.user_is_manager = self.env.user.has_group('wt_hewalat.wt_hewalat_manager')



    def action_search_wizard(self):
        action = self.env.ref('wt_hewalat.wt_hewalat_bank_transfers_search_action').read()[0]
        action.update({
            'target': 'new',
            'context': {
                'default_account_id': self.id,
                'default_bank_account': self.name,
                'default_bank': self.bank,
                'default_transfers_min_date': self.transfers_min_date,
                'default_transfers_max_date': self.transfers_max_date,
                'default_has_transfers': self.has_transfers,
                'default_user_is_manager': self.user_is_manager
            }
        })
        return action
        


    