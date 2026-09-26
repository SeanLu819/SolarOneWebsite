/**
 * ProductAdmin — hide detail-only form sections when the page layout is
 * "series overview".
 *
 * Fieldsets tagged with the `detail-only` class (dimension/beam-angle images,
 * Energy & Performance Data, legacy specs) are only rendered by
 * product_detail.html. When the editor picks `page_layout = overview` they are
 * hidden live; the underlying data is NEVER deleted — switching back to
 * `detail` brings the sections (and their values) straight back.
 *
 * 2026-09-26 fix: page_layout renders as a <select> dropdown (default admin
 * widget), NOT radio buttons — the old selector `input[name="page_layout"]`
 * matched nothing, so the hiding never fired. Now both widget types are
 * supported; ProductImagePath… admin tests pin this contract.
 */
(function () {
    'use strict';

    function currentValue() {
        var checked = document.querySelector('input[name="page_layout"]:checked');
        if (checked) {
            return checked.value;
        }
        var select = document.querySelector('select[name="page_layout"]');
        return select ? select.value : null;
    }

    function apply() {
        var isOverview = currentValue() === 'overview';
        document.querySelectorAll('fieldset.detail-only').forEach(function (fs) {
            fs.style.display = isOverview ? 'none' : '';
        });
    }

    function init() {
        var inputs = document.querySelectorAll(
            'input[name="page_layout"], select[name="page_layout"]');
        if (!inputs.length) {
            return; // not the product change form
        }
        inputs.forEach(function (el) {
            el.addEventListener('change', apply);
        });
        apply(); // honour the value already saved on this product
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
}());
