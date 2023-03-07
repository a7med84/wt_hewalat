# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from cryptography.fernet import Fernet
from ..utils.crypto import decrypt, get_key
import datetime

class BankTransfer(models.Model):
    _name = 'wt.hewalat.bank.transfer'
    _description = "Bank Transfer"
    _order ="date desc, credit desc"

    # common fields between all banks
    bank_account_id = fields.Many2one('wt.hewalat.bank.account', string='Bank', index=True, tracking=True, required=True, ondelete='cascade')
    date = fields.Char(string='Gregorian Date', tracking=True, required=True)
    details = fields.Char(string='Transfer Details', tracking=True, required=True)
    credit = fields.Char(string='Credit', tracking=True)
    debit = fields.Char(string='Debit', tracking=True)
    balance = fields.Char(string='Balance', tracking=True, required=True)

    date_comp = fields.Date(compute="_date_comp")
    details_comp = fields.Char(compute="_details_comp")
    credit_comp = fields.Float(compute="_credit_comp")
    debit_comp = fields.Float(compute="_debit_comp")
    balance_comp = fields.Char(compute="_balance_comp")

    # rajhi extra fields
    date_hijri = fields.Char(string='Hijri Date', tracking=True)
    time = fields.Char(string='Time', tracking=True)
    details_extra = fields.Char(string='Extra Details', tracking=True)
    channel = fields.Char(string='Channel', tracking=True)

    date_hijri_comp = fields.Char(compute="_date_hijri_comp")
    time_comp = fields.Char(compute="_time_comp", readonly=True)
    details_extra_comp = fields.Char(compute="_details_extra_comp", readonly=True)
    channel_comp = fields.Char(compute="_channel_comp", readonly=True)

    # ahly and inma extra fields
    reference = fields.Char(string='Refernce #', tracking=True)
    notes = fields.Char(string='Notes', tracking=True)

    reference_comp = fields.Char(compute="_reference_comp")
    notes_comp = fields.Char(compute="_notes_comp")

    # sab extra field
    currency = fields.Char(string='Credit currency', tracking=True)

    currency_comp = fields.Char(string='Credit currency', compute="_currency_comp")

    
    @api.depends('date')
    def _date_comp(self):
        for rec in self:
            val = rec.date
            val = decrypt(rec.date)
            val = datetime.datetime.strptime(val, "%d/%m/%Y")
            rec.date_comp = val

    @api.depends('details')
    def _details_comp(self):
        for rec in self:
            rec.details_comp = decrypt(rec.details)


    @api.depends('credit')
    def _credit_comp(self):
        for rec in self:
            rec.credit_comp = decrypt(rec.credit)

    @api.depends('debit')
    def _debit_comp(self):
        for rec in self:
            rec.debit_comp = decrypt(rec.debit)

    @api.depends('balance')
    def _balance_comp(self):
        for rec in self:
            rec.balance_comp = decrypt(rec.balance)


    @api.depends('date_hijri')
    def _date_hijri_comp(self):
        for rec in self:
            val = rec.date_hijri
            if val:
                rec.date_hijri_comp = decrypt(val)
            else:
                rec.date_hijri_comp = ""


    @api.depends('time')
    def _time_comp(self):
        for rec in self:
            val = rec.time
            if val:
                rec.time_comp = decrypt(val)
            else:
                rec.time_comp = ""


    @api.depends('details_extra')
    def _details_extra_comp(self):
        for rec in self:
            val = rec.details_extra
            if val:
                rec.details_extra_comp = decrypt(val)
            else:
                rec.details_extra_comp = ""


    @api.depends('channel')
    def _channel_comp(self):
        for rec in self:
            val = rec.channel
            if val:
                rec.channel_comp = decrypt(val)
            else:
                rec.channel_comp = ""

    @api.depends('reference')
    def _reference_comp(self):
        for rec in self:
            val = rec.reference
            if val:
                rec.reference_comp = decrypt(val)
            else:
                rec.reference_comp = ""

    @api.depends('notes')
    def _notes_comp(self):
        for rec in self:
            val = rec.notes
            if val:
                rec.notes_comp = decrypt(val)
            else:
                rec.notes_comp = ""
    
    
    @api.depends('currency')
    def _currency_comp(self):
        for rec in self:
            val = rec.currency
            if val:
                rec.currency_comp = decrypt(val)
            else:
                rec.currency_comp = "SAR"
                

    @api.model
    def create(self, vals):
        key = get_key()
        fernet = Fernet(key)
        for k, v in vals.items():
            if not v or k == 'bank_account_id':
                continue
            elif k in ['credit', 'debit', 'balance']:
                v = str(v).replace(',', '').replace('٬', '').replace('٫', '.')
            new_val = fernet.encrypt(str(v).encode())
            new_val = str(new_val, 'utf-8')
            vals[k] = new_val
        return super(BankTransfer, self).create(vals)
