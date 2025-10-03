# tell editor to where upload fields
CKEDITOR_UPLOAD_PATH = "ckeditor-files/"
CKEDITOR_UPLOAD_PATH = "public/ckeditor-files/"

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        # full list of CKEditor actions
        # https://ckeditor.com/old/forums/CKEditor/Complete-list-of-toolbar-items
        'toolbar_Custom': [
            ['Cut', 'Copy', 'Paste', 'Undo', 'Redo'],
            ['Bold', 'Italic', 'Underline', 'RemoveFormat', 'Strike'],
            [
                'NumberedList', 'BulletedList', '-',
                'JustifyLeft', 'JustifyCenter', 'JustifyRight',
                'JustifyBlock',
            ],
            ['Link', 'Unlink'],
            ['Table', 'HorizontalRule'],
            ['TextColor', 'FontSize', 'Format', "BGColor"],
            ['Image', 'Iframe'],
            ['Smiley', 'SpecialChar'],
            ['Source', 'Preview'],
        ],
        'full_page': True,
        'allowedContent': True,
        'width': '1200px',
        'height': '600px',
    }
}
