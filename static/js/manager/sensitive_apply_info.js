var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

function changeURL(menu) {
    history.pushState(null, '', window.location.pathname + '?' + 'menu=' + menu);
}

$(document).ready(function () {

    $('.hide_submit-check').on('click', function () {
        $('.submit-check').addClass('d-none')
    })

    $('.hide_submit-transfer').on('click', function () {
        $('.submit-transfer').addClass('d-none')
    })

    $('.hide_submit-partial-transfer').on('click', function () {
        $('.partial-pop').addClass('d-none')
    })

    $('.send-check').on('click', function () {
        let checked = true;

        if ((!$(`#reviewForm input[name=reviewer_name]`).val()) | (!$(`#reviewForm textarea[name=comment]`).val())) {
            checked = false;
        }

        if (checked) {
            $('.submit-check').removeClass('d-none')
        } else {
            alert('請完整填寫審核意見表格')
        }
    })

    $('.send_review').on('click', function () {
        $.ajax({
            url: "/submit_sensitive_response",
            type: 'POST',
            data: $('#reviewForm').serialize() + '&csrfmiddlewaretoken=' + $csrf_token,
            dataType: 'json'
        })
        .done(function (response) {
            alert('送出成功')
            window.location.reload()
        })
        .fail(function (xhr, status, errorThrown) {
            alert(gettext('發生未知錯誤！請聯絡管理員'))
            console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })
    })

    $('.applicant_refs').on('click', function(){
        $("#downloadApplicantReport").submit()
    })


    $('.send-transfer').on('click', function () {
        $('.submit-transfer').removeClass('d-none')
    })

    $('.send-partial-transfer').on('click', function () {
        $('.partial-pop').removeClass('d-none')
    })



    $('.transferRequest').on('click', function () {
        $.ajax({
            url: "/transfer_sensitive_response",
            type: 'POST',
            data: { 'query_id': $('#reviewForm input[name=query_id]').val(), csrfmiddlewaretoken: $csrf_token },
            dataType: 'json'
        })
        .done(function (response) {
            alert('轉交成功')
            window.location.reload()
        })
        .fail(function (xhr, status, errorThrown) {
            alert(gettext('發生未知錯誤！請聯絡管理員'))
            console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })
    })


    $('.partialTransferRequest').on('click', function () {
        $.ajax({
            url: "/partial_transfer_sensitive_response",
            type: 'POST',
            data: { 'query_id': $('#reviewForm input[name=query_id]').val(), 
                    'partner_id': $('select[name=partial_partner_id]').find(":selected").val(),
                    'is_last_one': $('select[name=partial_partner_id] option').length == 1 ? true : false,
                    csrfmiddlewaretoken: $csrf_token },
            dataType: 'json'
        })
        .done(function (response) {
            alert('轉交成功')
            window.location.reload()
        })
        .fail(function (xhr, status, errorThrown) {
            alert(gettext('發生未知錯誤！請聯絡管理員'))
            console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })
    })

})


