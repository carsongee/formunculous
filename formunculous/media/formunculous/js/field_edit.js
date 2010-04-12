jQuery(document).ready(function($)
{

	$('#dropdown_dialog').dialog({
		autoOpen: false,
		modal: true,
		width: 500,
		height: 400,
		buttons: {
			"Close": function() {
				$(this).dialog("close");
			}
		},
		bgiframe: true
	});

	$(".formunculous_field_list").sortable({
		placeholder: 'ui-state-highlight',
		stop: function(event,ui) {

			//Check if we are adding a new element
			if(ui.item.hasClass('formunculous-new-field'))
			{
				add_field(ui.item);
			}
			
			sort_fields();
		}
	});
	$(".formunculous_field_head").children().disableSelection();

	// Connect the field types to the field list for drag/drop adding
	// of fields.
	$('.formunculous_field_types li').draggable({
		connectToSortable: '.formunculous_field_list',
		helper: 'clone'
	});
	$('.formunculous_field_types li').disableSelection();


	// Handle expanding and collapsing
	$('.formunculous_field_body').hide();

	$(".formunculous_field_list").click(function(e)
	{
		if($(e.target).is('.formunculous_field_collapse') || $(e.target).is('.formunculous_field_title') || $(e.target).is('.formunculous_field_name')) {

			if($(e.target).is('.formunculous_field_title')) {
				j = $(e.target).find('.formunculous_field_collapse');
			}
			else if($(e.target).is('.formunculous_field_name')) {
				j = $(e.target).parent().find('.formunculous_field_collapse')
			}
			else {
				j = $(e.target);
			}
			

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
			jn = j.parents('.formunculous_field_head')
			jn.next(".formunculous_field_body").slideToggle(300);
		}
	});

// Register event handlers
hide_delete_box();
delete_field();
add_above();
add_below();

urlify_slug();
dropdown();


});

function hide_delete_box() {
	// Hide all the delete checkboxes
	$('input').filter(function() {
					return this.id.match(/id_fielddefinition_set-\d+-DELETE/);
	}).hide();
}

function urlify_slug() {
	// URLify label -> slug
	$('input').filter(function() {
		return this.id.match(/id_fielddefinition_set-\d+-slug/);
	}).change(function() {
		this._changed = true;
	});
	$('input').filter(function() {
		return this.id.match(/id_fielddefinition_set-\d+-label/);
	}).unbind('keyup').keyup(function() {
		//URLify the slug
		e = $(this).parents('.formunculous_field_body').find('input').filter(function() {
			return this.id.match(/id_fielddefinition_set-\d+-slug/);
		});
		if(!e._changed)
		{
			e.attr({value: URLify($(this).attr('value'), 50)});
		}
		
		//Change the field title
		$(this).parents('.formunculous_field_body')
			.prev('.formunculous_field_head').find('.formunculous_field_name')
			.html($(this).val());
	});
}

// delete a field
function delete_field() {
	$('.formunculous_field_delete').unbind('click').click(function() {
		body = $(this).parents('.formunculous_field_actions').parents('li').children('.formunculous_field_body');
		check = body.find('input').filter(function() {
				return this.id.match(/id_fielddefinition_set-\d+-DELETE/);
		});

		if(confirm('Are you sure you want to delete this field?\n'))
		{
			// Already an existing field, so mark to delete
			if(check.size() > 0)
			{
				$(check).attr('checked', true);
				$(check).parents('li').hide('fold', {},750);
			}
			else
			{
				// Newly added field, delete the HTML and
				// decrement the TOTAL_FORMS count
				var formCount = parseInt($('#id_fielddefinition_set-TOTAL_FORMS').val());
				$('#id_fieldefinition_set-TOTAL_FORMS').val(formCount - 1);
				$(body).parents('li').hide('fold', {}, 750, function() {
					$(this).remove();
				});
			}
		}
	});
}


function dropdown() {
	$('.formunculous_field_dropdown').unbind('click').click(function() {
		// Setup the dialog box iframe and display it
		var id = $(this).parents('.formunculous_field_body').find('input').filter(
			function() {
			return this.id.match(/id_fielddefinition_set-\d+-id/);
			});
		var content = ""
		if(! id.val()) {
			content = "<p>You must save the field definition before you add/modify dropdown selections</p>";
		}
		else {
			content = '<iframe frameborder="0" style="border: 0;" src="' + drop_down_url + '?id=' + id.val() + '"';
			content += 'width="100%" height="90%"> <p>Your browser doesn\'t support iframes.</p>';
			content += '</iframe>';
		}
		$('#dropdown_dialog').html(content);
		$('#dropdown_dialog').dialog('open');
	});
}

// Register the add above event
function add_above() {
	$('.formunculous_field_add_above').unbind('click').click(function() {
		// Call add_field with the newly created 'before' li item.
		var el = $(this).parents('.formunculous_field_actions').parents('li').before('<li class="formunculous-new-field">New Item</li>');
		add_field(el.prev());
	});

	// Because the sorter event isn't called, filling in the order field
	// must be done manually
	sort_fields();
}

// Register the add below event
function add_below() {
	$('.formunculous_field_add_below').unbind('click').click(function() {
		// Call add_field with the newly created 'after' li item.
		var el = $(this).parents('.formunculous_field_actions').parents('li').after('<li class="formunculous-new-field">New Item</li>');
		add_field(el.next());
	});
	// Because the sorter event isn't called, filling in the order field
	// must be done manually
	sort_fields();
}


function fix_form_index(new_field){
	var prefix = 'fielddefinition_set';
	var formCount = parseInt($('#id_' + prefix + '-TOTAL_FORMS').val());
	new_field.find('*').each( function() {
		var id_regex = new RegExp('(' + prefix + '-\\d+)');
		var replacement = prefix + '-' + formCount;
		if ($(this).attr("for")) $(this).attr("for", $(this).attr("for").replace(id_regex, replacement));
		if (this.id) this.id = this.id.replace(id_regex, replacement);
		if (this.name) this.name = this.name.replace(id_regex, replacement);
	});
	$('#id_' + prefix + '-TOTAL_FORMS').val(formCount + 1);
}

function sort_fields() {
	// Sorting has occurred renumber the order
	// field for each of the fielddefinitions
	var i = 0;
	$('.formunculous_field_body').each(function() {
		order = $(this).find('input').filter(function() {
			return this.id.match(/id_fielddefinition_set-\d+-order/);
		});
		order.attr({value: i});
		i++;
	});
}

function add_field(item) {
	var ajax_response = null;
	$.ajax({
		url: new_form_url,
		type: "GET",
		datatype: "html",
		async: false,
		success: function(data) {
			ajax_response = data;
		}
	});
	if( ajax_response != null )
	{
		
		// Grab slug/name
		item.before(ajax_response);

		new_elem = item.prev();

		//Replace counters and increment form count
		fix_form_index(new_elem.find('.formunculous_field_body'));

		//Set value for field type
		var field_type = item.find('.field_type_selection').html();
		if(field_type)
		{
			new_elem.find('*').filter( function() {
				return this.id.match(/id_fielddefinition_set-\d+-type/);
			}).val(field_type);
		}
		
		//Register slug-name combo and actions
		urlify_slug();
		delete_field();
		add_above();
		add_below();
		dropdown();

		//Hide Delete Box and change CSS arrow
		hide_delete_box();
		
		arrow = new_elem.find('.formunculous_field_collapse').css('background-image')
		arrow = arrow.replace('arrow-down.gif', 'arrow-up.gif');
		new_elem.find('.formunculous_field_collapse').css({backgroundImage: arrow })
		
		// Removed cloned draggable
		item.remove();
					
		// Focus on the label field
		new_elem.find('input').filter(function() {
			return this.id.match(/id_fielddefinition_set-\d+-label/);
		}).focus();
	} else {
		alert('Unable to add a new field');
	}
}