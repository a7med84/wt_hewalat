// define odoo module
odoo.define('wt_hewalat.LimitUploadSize', ['web.field_registry', 'web.basic_fields', 'web.core'], function (require) {
    "use strict";

    // require needed packages
    let fieldRegistry = require('web.field_registry');
    let basicFields = require('web.basic_fields');
    // core._t for translation
    let core = require('web.core');
    let _t = core._t;

    // extend binary field
    var BinaryFileLimitSizeAndType = basicFields.FieldBinaryFile.extend({
        // binary field already checking for max_upload_size which is set to 128 * 1024 * 1024
        // override its value in init twith the size set in attrs
        init: function (parent, name, record) {
            // call super first in init fo default initiation
            this._super.apply(this, arguments);

            if(this.attrs.max_upload_size) {
                console.log(this.attrs.max_upload_size)
                this.max_upload_size = this.attrs.max_upload_size;
            }
            
        },
        // binary field not checking for file type so add a check on on change
        on_file_change: function (e) {
            let self = this;
            let file_node = e.target;
            if ((this.useFileAPI && file_node.files.length) || (!this.useFileAPI && $(file_node).val() !== '')) {
                let file = file_node.files[0];
                if (file.type !=  this.attrs.mimetype) {
                    var msg = _t("The selected file must be of type %s.");
                    this.do_warn(_t("File upload"), _.str.sprintf(msg, this.attrs.mimetype));
                    return false;
                }
            }
            // call super at the end to complete default handling after added check
            this._super.apply(this, arguments);
        },
    });
    
    fieldRegistry.add('file_widget_limit_size_and_type', BinaryFileLimitSizeAndType);

});