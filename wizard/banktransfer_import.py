# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import ValidationError, UserError
from lxml import etree
import base64
import io
import pandas as pd

Max_UPLOAD_SIZE = "5242880"
MIMETYPE = "text/csv"

class BanktransferImportWizard(models.TransientModel):
    _name = "wt.hewalat.banktransfer.import.wizard"
    _description = "Banktransfer import wizard"

    
    transfers_file = fields.Binary(required=True)
    file_name = fields.Char()
    bank_account_id = fields.Many2one(
        string='Bank Account',
        comodel_name='wt.hewalat.bank.account',
        ondelete='restrict',
        required=True
    )

    date_format = fields.Selection(
        required=True,
        selection=[
            ('%d/%m/%Y', 'Day First'),
            ('%m/%d/%Y', 'Month First'),
            ],
        )
    

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(BanktransferImportWizard, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(result['arch'])
            _file = doc.xpath("//field[@name='transfers_file']")
            if _file:
                _file[0].set("max_upload_size", Max_UPLOAD_SIZE)
                _file[0].set("mimetype", MIMETYPE)
                result['arch'] = etree.tostring(doc, encoding='unicode')
        return result



    def action_import(self):
        data = self.read(['bank_account_id', 'date_format', 'transfers_file', 'file_name'])[0]

        if not data['file_name']:
            raise UserError(_('No file selected!!'))

        if data['file_name'].split('.')[-1] != 'csv':
            raise ValidationError(_('The selected file must be of type "csv"'))
        
        account = self.env['wt.hewalat.bank.account'].browse(data['bank_account_id'][0])
        # each bank has a different statement with different columns' names 
        # and order and different date and number formats
        # so each bank has a different validation function
        # chack the bank and make sure a validation function is defined
        if account.bank == "الراجحي":
            validate_df = self._validate_rajhi
        elif account.bank == "الأهلي":
            validate_df = self._validate_ahly
        elif account.bank == "الانماء":
            validate_df = self._validate_inma
        elif account.bank == "البلاد":
            validate_df = self._validate_belad
        elif account.bank == "ساب":
            validate_df = self._validate_sab
        else:
           # if unknow banl raise error
           raise UserError(_('Adding transfers is not implemented for bank ' + account.bank))
      
        # create df, check if not empty or file not corrupted
        # all types object so validation 
        try:
            with io.BytesIO(base64.b64decode(data['transfers_file'])) as f:
                df = pd.read_csv(f, dtype=str)
        except Exception as e:
            raise ValidationError(_('ERROR while readig the file: ') + str(e))

        if df.size <0 :
            raise ValidationError(_('The file is empty!!'))
        
        df.columns = [col.strip() for col in df.columns]
        df = validate_df(account, df, data['date_format'])
 
        transfers = self.env['wt.hewalat.bank.transfer'].create(df.to_dict(orient="records"))
        action = self.env.ref('wt_hewalat.wt_hewalat_bank_transfers_action').read()[0]
        action.update({
            'domain': [('id', 'in', transfers.ids)],
            'help': """<p class="o_view_nocontent_neutral_face">{}</p>""".format(_('No Results')),
        })
        return action

        

    def _validate_rajhi(self, bank_account, df, date_format):
        # rename columns
        try:
            df = df.rename(errors='raise', columns={
            'نوع قناة الاتصال': 'channel',
            'الرصيد': 'balance',
            'مدين': 'debit',
            'دائن': 'credit',
            'ملاحظات': 'details',
            'التفاصيل': 'details_extra',
            'الوقت': 'time',
            'التاريخ الهجري': 'date_hijri',
            'التاريخ الميلادي': 'date',
            })
        except KeyError as e:
            raise ValidationError(_("ERROR columns: ") + str(e))
    
        df = self._common_validation(bank_account, df, date_format)
        df = self._credit_debit_validation(df)
        return df.astype('str')
        
        

    def _validate_ahly(self, bank_account, df, date_format):
        # rename columns
        try:
            df = df.rename(errors='raise', columns={
                'التاريخ': 'date',
                'التفاصيل': 'details_extra',
                'الوصف': 'details',
                'تفاصيل إضافية': 'notes',
                'المرجع': 'reference',
                'ملاحظات': 'channel',
                'مدين': 'debit',
                'دائن': 'credit',
                'الرصيد': 'balance',
            })
        except KeyError as e:
            raise ValidationError(_("ERROR columns: ") + str(e))
    
        df = self._common_validation(bank_account, df, date_format)
        df = self._credit_debit_validation(df)
        self._validate_reference(df)
        return df.astype('str')
        

    def _validate_inma(self, bank_account, df, date_format):
        # inma statments have some empty columns named Unamed{n}
        df = df[[col for col in df.columns if not 'Unnamed' in col]]
        # rename columns
        try:
            df = df.rename(errors='raise', columns={
                'الرصيد\nBalance': 'balance',
                'دائن/مدين\nCredit/Debit': 'credit',
                'تفاصيل العملية\nTransaction Description': 'details',
                'الرقم المرجعي\n# Reference': 'reference',
                'تاريخ العملية\nTransaction Date': 'date',  
            })
        except KeyError as e:
            raise ValidationError(_("ERROR columns: ") + str(e)) 
        
        self._validate_reference(df)
        
        if df.credit.isna().sum():
            raise ValidationError(_("ERROR: Some rows have empty credit"))
        df['debit'] = "0"
        df = self._common_validation(bank_account, df, date_format)
        return df.astype('str')
    

    def _validate_belad(self, bank_account, df, date_format):
        # rename columns
        try:
            df = df.rename(errors='raise', columns={
                'التاريخ': 'date',
                'التاريخ الهجري': 'date_hijri',
                'مدين': 'debit',
                'دائن': 'credit',
                'الرصيد': 'balance',
                'رقم المرجع': 'reference',
                'الوصف': 'details_extra',
                'التفاصيل': 'details',
            })
        except KeyError as e:
            raise ValidationError(_("ERROR columns: ") + str(e))
    
        df = self._common_validation(bank_account, df, date_format)
        df = self._credit_debit_validation(df)
        self._validate_reference(df)
        return df.astype('str')
    

    def _validate_sab(self, bank_account, df, date_format):
        # inma statments have some empty columns named Unamed{n}
        df = df[[col for col in df.columns if not 'Unnamed' in col]]
        # rename columns
        try:
            df = df.rename(errors='raise', columns={
                'المبلغ المحول/المسحوب': 'credit',
                'الرصيد': 'balance',
                'التعليقات': 'details',
                'تاريخ التحويل': 'date',
                'الرقم التسلسلي': 'reference',
            })
        except KeyError as e:
            raise ValidationError(_("ERROR columns: ") + str(e)) 
        
        self._validate_reference(df)
        
        if df.credit.isna().sum():
            raise ValidationError(_("ERROR: Some rows have empty credit"))
        

        df[['credit', 'currency']] = df.credit.str.split(" ", expand = True)
        df['debit'] = "0"
        df = self._common_validation(bank_account, df, date_format, False)
        return df.astype('str')


    
    def _common_validation(self, bank_account, df, date_format, validate_numbers=True):
        if df.details.isna().sum():
            raise ValidationError(_("ERROR: Some rows have empty details"))
        
        if df.balance.isna().sum():
            raise ValidationError(_("ERROR: Some rows have empty balance"))
        
        if df.date.isna().sum():
            raise ValidationError(_("ERROR: Some rows have empty date"))
        
        if validate_numbers:
            try:
                for col in ['credit', 'debit', 'balance']:
                    df[col] = df[col].str.replace(r'[,٬]', '', regex=True)
                    df[col] = df[col].str.replace('٫', '.', regex=False).astype(float)
            except:
                raise ValidationError(_("ERROR: Invalid number format: " + col))

        df.date = df.date.str.replace(r'-', '/')
        df.date = df.date.str.replace('\\', '/', regex=True)
        try:
            df.date = pd.to_datetime(df.date, format=date_format)
        except ValueError as e:
            try:
                date_format_reversed = '/'.join(date_format.split('/')[::-1])
                df.date = pd.to_datetime(df.date, format=date_format_reversed)
            except ValueError as e:
                raise ValidationError(_("ERROR: date format used in the selected file does not match the date format field"))
            
        df.date = df.date.dt.strftime('%d/%m/%Y')
        df['bank_account_id'] = bank_account.id
        return df
    

    def _credit_debit_validation(self, df):
        if (df.credit.isna().sum() != df.debit.notna().sum()) | (df.credit.notna().sum() != df.debit.isna().sum()):
            raise ValidationError(_("ERROR: Credit or debit columns values not correct"))
        else:
            df = df.fillna({
                "credit":0,
                "debit":0,
            })
        return df

    
    def _validate_reference(self, df):
        if df.reference.isna().sum():
            raise ValidationError(_("ERROR: Some rows have empty reference"))
        