$(function () {
    $('.contact_partner').on('click', function () {
        $('.feedback-pop select[name="partner_id"]').val($(this).data('partner_id'));
        $('.feedback-pop').removeClass('d-none')
    })
})
