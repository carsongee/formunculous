jQuery(document).ready(function($)
{
	$("#formunculous-apply-review-forms").hide();

	$(".formunculous_currentlink").click(function() {
			$("#formunculous-apply-review-forms").hide();
			$("#formunculous-apply-available-forms").fadeIn(300);
			$("#formunculous-review").removeClass("here");
			$("#formunculous-current").addClass("here")

		});
	$(".formunculous_reviewlink").click(function() {
			$("#formunculous-apply-available-forms").hide();
			$("#formunculous-apply-review-forms").fadeIn(300);
			$("#formunculous-current").removeClass("here");
			$("#formunculous-review").addClass("here")
		});

});
