jQuery(document).ready(function($)
{
	$(".apply_sub_form_title").click(function(e)
	{
		if($(e.target).is('.apply_sub_form_field_collapse')) {
			j = $(e.target);

			if( j.css('background-image').indexOf('img/arrow-down.gif') > -1)
			{
				arrow = j.css('background-image')
				arrow = arrow.replace('arrow-down.gif', 'arrow-up.gif');
				j.css({backgroundImage: arrow })
			}
			else
			{
				arrow = j.css('background-image')
				arrow = arrow.replace('arrow-up.gif', 'arrow-down.gif');
				j.css({backgroundImage: arrow })
			}
			jn = j.parents('.apply_sub_form_title');
			jn.next(".apply_sub_form_body").slideToggle(300);
		}
	});

});