CKEDITOR.editorConfig = function( config )
{
	config.toolbar = 'Full';

	config.toolbar_Full =
	[
	 ['Source','-','Save','NewPage','Preview','-','Templates'],

	 ['Cut','Copy','Paste','PasteText','PasteFromWord','-','Print',
	 'SpellChecker', 'Scayt'],

	 ['Undo','Redo','-','Find','Replace','-','SelectAll','RemoveFormat'],

	 '/',

	 ['Bold','Italic','Underline','Strike','-','Subscript','Superscript'],

	 ['NumberedList','BulletedList','-','Outdent','Indent','Blockquote'],

	 ['JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock'],

	 ['Link','Unlink','Anchor'],

	 ['Image','Flash','Table','HorizontalRule','Smiley',
	  'SpecialChar','PageBreak'],

	 '/',

	 ['Styles','Format','Font','FontSize'],

	 ['TextColor','BGColor'], ['Maximize', 'ShowBlocks','-','About']

	 ];
};

