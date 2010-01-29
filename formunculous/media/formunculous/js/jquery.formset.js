/**
 * jQuery Formset 1.1
 * @author Stanislaus Madueke (stan DOT madueke AT gmail DOT com)
 * @requires jQuery 1.2.6 or later
 *
 * Copyright (c) 2009, Stanislaus Madueke
 * All rights reserved.
 *
 * Licensed under the New BSD License
 * See: http://www.opensource.org/licenses/bsd-license.php
 */
(function($) {
    $.fn.formset = function(opts)
    {
        var options = $.extend({}, $.fn.formset.defaults, opts);

        var updateElementIndex = function(el, prefix, ndx) {
            var id_regex = new RegExp('(' + prefix + '-\\d+)');
            var replacement = prefix + '-' + ndx;
            if ($(el).attr("for")) $(el).attr("for", $(el).attr("for").replace(id_regex, replacement));
            if (el.id) el.id = el.id.replace(id_regex, replacement);
            if (el.name) el.name = el.name.replace(id_regex, replacement);
        };

        $(this).each(function(i) {
            $(this).addClass(options.formCssClass);
        });

        if ($(this).length) {
            var $addBtn;
            if ($(this).attr('tagName') == 'TR') {
                // If forms are laid out as table rows, insert the
                // "add" button in a new table row:
                var numCols = this.eq(0).children().length;
                $(this).parent().append('<tr><td colspan="' + numCols + '"><a class="' + options.addCssClass + '" href="javascript:void(0)">' + options.addText + '</a></tr>');
                $addBtn = $(this).parent().find('tr:last a');
            } else {
                // Otherwise, insert it immediately after the last form:
                $(this).filter(':last').after('<a class="' + options.addCssClass + '" href="javascript:void(0)">' + options.addText + '</a>');
                $addBtn = $(this).filter(':last').next();
            }
            $addBtn.click(function() {
                var nextIndex = parseInt($('#id_' + options.prefix + '-TOTAL_FORMS').val());
				if( (nextIndex+1) > options.maxForms && 0!=options.maxForms )
				{
					alert(options.alertText);
					return false;
				}
                var row = $('.' + options.formCssClass + ':first').clone(true).get(0);
                $(row).removeAttr('id').insertAfter($('.' + options.formCssClass + ':last'));
                $(row).find('input,select,textarea,label').each(function() {
                    updateElementIndex(this, options.prefix, nextIndex);
                    // If this is a checkbox or radiobutton, set uncheck it.
                    // Fix for Issue 1, reported by Wilson.Andrew.J:
                    var elem = $(this);
                    if (elem.is('input:checkbox') || elem.is('input:radio')) {
                        elem.attr('checked', false);
                    } else {
                        elem.val('');
                    }
                });
                var formCount = nextIndex + 1;
                $('#id_' + options.prefix + '-TOTAL_FORMS').val(formCount);
                // If we've got more than one form, enable delete buttons:
                //if (formCount > 1) { $('a.' + options.deleteCssClass).show(); }
                // If a post-add callback was supplied, call it with the added form:
                if (options.added) options.added($(row), formCount);
                return false;
            });
        }

        // If the formset is initialized with a single form, hide the delete button:
        if ($(this).length == 1) { $('a.' + options.deleteCssClass).hide(); }

        return $(this);
    }

    /* Setup plugin defaults */
    $.fn.formset.defaults = {
        prefix: 'form',                  // The form prefix for your django formset
        addText: 'add another',          // Text for the add link
        deleteText: 'remove',            // Text for the delete link
        addCssClass: 'add-row',          // CSS class applied to the add link
        deleteCssClass: 'delete-row',    // CSS class applied to the delete link
        formCssClass: 'dynamic-form',    // CSS class applied to each form in a formset
        added: null,                     // Function called each time a new form is added
        removed: null                    // Function called each time a form is deleted
    }
})(jQuery)
