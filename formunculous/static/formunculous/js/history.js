jQuery(document).ready(function($)
{
	$(".formunculous_history_bar").hide();

	$(".formunculous_currentlink").click(function() {
			$(".formunculous_history_bar").hide();
			$(".formunculous_container").fadeIn(300);
			$("#formunculous-history").removeClass("here");
			$("#formunculous-current").addClass("here")

		});
	$(".formunculous_historylink").click(function() {
			$(".formunculous_container").hide();
			$(".formunculous_history_list ul li").each(function(){jQuery(this).removeClass("here");});
			$("#formunculous-history-app").html("");
			$(".formunculous_history_bar").fadeIn(300);
			$("#formunculous-history").addClass("here");
			$("#formunculous-current").removeClass("here")

		});

});

function getHistory(id, obj) {

	var successful = false;
	jQuery.ajax({
 			    url: historyURL,
				type: "POST",
				async: false,
				cache: false,
				timeout: 10000,
				data: { app: id },
				datatype: "html",
				success: function(data)  {
				  jQuery("#formunculous-history-app").html(data);
				  successful = true;
			    },
				error: function() {
				    jQuery("#formunculous-history-app").html("Unable to retrieve the form");
					successful = false;
			    }
		});

	if(successful==true) {
		jQuery(".formunculous_history_list ul li").each(function(){jQuery(this).removeClass("here");});
		jQuery(obj).parent().addClass("here")
	}
}