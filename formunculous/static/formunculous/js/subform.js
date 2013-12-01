jQuery(document).ready(function($)
{
	$('#add_subform_dialog').dialog( {
		autoOpen: false,
		modal: true,
		width: 500,
		height: 600,
		
		buttons: {
			"Close": function() {
				$(this).dialog("close");
			},
			"Create": function() {
				$.ajax({
						url: new_subapp_url,
						type: "POST",
						data: { 
							ad: $('#subform_ad').attr('value'),
							name: $('#id_subform_name').attr('value'),
							slug: $('#id_subform_slug').attr('value'),
							min_entries: $('#id_min_entries').attr('value'),
							max_entries: $('#id_max_entries').attr('value'),
							extras: $('#id_extras').attr('value')
					    },
						datatype: "html",
						success: function(data)
						{
							$('.formunculous_table > tbody:last').append(data);
							$('.formunculous_table > tbody tr:last').effect('pulsate',{ times: 1},750);
							$('#add_subform_dialog').dialog("close");
							$('#ajax_results').html("<p>Successfully added the sub-form.</p>");
							$('#ajax_results').effect('highlight',{}, 1500);
						},
					    error: function(data) {
							$('#add_subform_dialog').dialog("close");
							$('#ajax_results').html("<p>Unable to create a sub-form.  Please check your inputs and try again");
							$('#ajax_results').effect('highlight',{},1500);
						}
					});
						  
			},
			"Create and Edit": function() {
				$.ajax({
						url: new_subapp_url,
						type: "POST",
						data: { 
							ad: $('#subform_ad').attr('value'),
							name: $('#id_subform_name').attr('value'),
							slug: $('#id_subform_slug').attr('value'),
							min_entries: $('#id_min_entries').attr('value'),
							max_entries: $('#id_max_entries').attr('value'),
							extras: $('#id_extras').attr('value')
					    },
						datatype: "html",
						success: function(data)
						{
							window.location = builder_index_url +
								"/fields/" 
								+ $('#id_subform_slug').attr('value') + '/';
						},
					    error: function(data) {
							$('#add_subform_dialog').dialog("close");
							$('#ajax_results').html("<p>Unable to create a sub-form.  Please check your inputs and try again");
							$('#ajax_results').effect('highlight',{},1500);
						}
					});

			}

		},
		bgiframe: true	
	});

	$('.formunculous_subform_add').click( function(){
			//Clear existing values
			$('#id_subform_name').attr('value', '');
			$('#id_subform_slug').attr('value', '');
			$('#id_min_entries').attr('value', '');
			$('#id_max_entries').attr('value', '');
			$('#id_extras').attr('value', '');
			
			$('#id_subform_name').focus();
			$('#add_subform_dialog').dialog('open');
			
	});


     document.getElementById("id_subform_slug").onchange = function() { this._changed = true; };
    
    document.getElementById("id_subform_name").onkeyup = function() {
        var e = document.getElementById("id_subform_slug");
        if (!e._changed) { e.value = URLify(document.getElementById("id_subform_name").value, 50); }
    }


	$('#change_subform_dialog').dialog( {
		autoOpen: false,
		modal: true,
		width: 500,
		height: 600,
		
		buttons: {
			"Close": function() {
				$(this).dialog("close");
			},
			"Change": function() {
				$.ajax({
						url: change_subapp_url,
						type: "POST",
						data: { 
							sad: current_app_id,
							name: $('#id_change_subform_name').attr('value'),
							slug: $('#id_change_subform_slug').attr('value'),
							min_entries: $('#id_change_min_entries').attr('value'),
							max_entries: $('#id_change_max_entries').attr('value'),
							extras: $('#id_change_extras').attr('value')
					    },
						datatype: "html",
						success: function(data)
						{
							$('#change_subform_dialog').dialog("close");
							$('#' + current_app_id).before(data).remove();
							$('#ajax_results').html("<p>Successfully modified the sub-form.</p>");
							$('#ajax_results').effect('highlight',{}, 1500);
						},
					    error: function(data) {
							$('#change_subform_dialog').dialog("close");
							$('#ajax_results').html("<p>Unable to change the sub-form.  Please check your inputs and try again");
							$('#ajax_results').effect('highlight',{},1500);
						}
					});
						  
			}

		},
		bgiframe: true
	});


    document.getElementById("id_change_subform_slug").onchange = function() { this._changed = true; };
    
    document.getElementById("id_change_subform_name").onkeyup = function() {
        var e = document.getElementById("id_change_subform_slug");
        if (!e._changed) { e.value = URLify(document.getElementById("id_change_subform_name").value, 50); }
    }


	// Delete Dialog Handling
	$('#del_dialog').dialog({
       autoOpen: false,
       modal: true,
       width: 300,
       buttons: {
         "OK": function() {
			 $('#ajax_results').load( 
					delete_subapp_url, 
					{ ad: current_app_id},
					function() {
						$('#' + current_app_id).fadeOut(1000,
						  function() {
							   $(this).remove(); 
							   $('#ajax_results').effect('highlight',{},1000);
						  });
					});
			 $(this).dialog("close");
		 },
         "Cancel": function() {
			 $(this).dialog("close");
		 }
	   },
       show: 'drop',
       bgiframe: true
});


});


var current_app_id = 0;


function show_change_dialog(id)
{
	current_app_id = id;
	// Get and populate the values of the change form by grabbing them out
	// of the table. I could use an AJAX to pull these from the database,
	// but this should save some time and it is really just a convenience to
	// provide the values..
	row = $("#" + id );

	name = row.find("td");
	$('#id_change_subform_name').attr("value", jQuery.trim(name.html()));

	slug = URLify(name.html(), 50);
	$('#id_change_subform_slug').attr("value", slug);

	min_entries = name.next();
	$('#id_change_min_entries').attr("value", jQuery.trim(min_entries.html()));

	max_entries = min_entries.next();
	$("#id_change_max_entries").attr("value", jQuery.trim(max_entries.html()));

	extras = max_entries.next();
	$("#id_change_extras").attr("value", jQuery.trim(extras.html()));

	$('#change_subform_dialog').dialog('open');
}

function show_delete_dialog(id)
{
    current_app_id = id;
    $("#del_dialog").dialog('open');
}

