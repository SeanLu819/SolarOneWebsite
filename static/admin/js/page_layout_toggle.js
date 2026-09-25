/**
 * ProductAdmin — hide detail-only form sections when the page layout is
 * "series overview".
 *
 * Fieldsets tagged with the `detail-only` class (dimension/beam-angle images,
 * Energy & Performance Data, legacy specs) are only rendered by
 * product_detail.html. When the editor picks `page_layout = overview` they are
 * hidden live; the underlying data is NEVER deleted — switching back to
 * `detail` brings the sections (and their values) straight back.
 */
(function () {
    'use strict';

    function apply() {
        var checked = document.querySelector(
            'input[name="page_layout"]:checked');
        var isOverview = checked && checked.value === 'overview';
        document.querySelectorAll('fieldset.detail-only').forEach(function (fs) {
            fs.style.display = isOverview ? 'none' : '';
        });
    }

    function init() {
        var inputs = document.querySelectorAll('input[name="page_layout"]');
        if (!inputs.length) {
            return; // not the product change form
        }
        inputs.forEach(function (input) {
            input.addEventListener('change', apply);
        });
        apply(); // honour the value already saved on this product
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
}());
