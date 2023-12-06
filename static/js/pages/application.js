var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");


$(function () {

    $('.sendRequest').on('click', function () {
        sendRequest()
    })

    $('#appilcationForm .inpu_2 .input_item select[name=type]').on('change', function () {
        if ($('#appilcationForm .inpu_2 .input_item select[name=type]').val() == '1') {
            $('.p_affli').removeClass('d-none')
            $('.project_type').html(`<span class="color_red">*</span>${gettext('委辦工作計畫名稱')}`)
        } else {
            $('.p_affli').addClass('d-none')
            $('.project_type').html(`<span class="color_red">*</span>${gettext('個人研究計畫名稱')}`)

        }
    })

    $('.item_set1 .add').on('click', function () {
        $('.apply_peo').append(`
        <div class="item_set1">
            <input type="text" name="user" placeholder="${gettext('姓名')}">
            <input type="text" name="user_affiliation" placeholder="${gettext('單位')}">
            <input type="text" name="user_job_title" placeholder="${gettext('職稱')}">
            <button class="delete">
                <div class="line1"></div>
            </button>
        </div>`)

        $('.delete').on('click', function () {
            $(this).parent().remove()
        })
    })

    // 申請資料使用者在送出的時候就先整理好成dict list

    let selectBox = new vanillaSelectBox("#apply_type", {
        "placeHolder": gettext("計畫類型"), search: false, disableSelectAll: true,
    });

    $('#appilcationForm .vsb-main button').css('border', '').css('background', '')
    // $('#appilcationForm span.caret').addClass('d-none')

    $('#appilcationForm .vsb-main button').on('click', function () {
        if ($(this).next('#appilcationForm .vsb-menu').css('visibility') == 'visible') {
            $(this).next('#appilcationForm .vsb-menu').addClass('visible')
        } else {
            $(this).next('#appilcationForm .vsb-menu').css('visibility', '')
            $(this).next('#appilcationForm .vsb-menu').removeClass('visible')
        }
    })

    selectBox.setValue('0')
    $('#btn-group-apply_type button span.title').addClass('black')

    $('#apply_type').on('change', function () {
        if ($('#btn-group-apply_type .vsb-menu ul li.active').length > 0) {
            $('#btn-group-apply_type button span.title').addClass('black').removeClass('color-707070')
        } else {
            $('#btn-group-apply_type button span.title').addClass('color-707070').removeClass('black')
        }
    })


})

function sendRequest() {
    //alert($('#appilcationForm').serialize())
    if ($('input[name=is_authenticated]').val() == 'True') {

        let checked = true;

        let users = [];
        $('.apply_peo .item_set1').each(function () {
            if ( // 如果不是全空才加上去
                !((!$(this).children('input[name=user]').val()) & (!$(this).children('input[name=user_affiliation]').val()) & (!$(this).children('input[name=user_job_title]').val()))
            ) {
                users.push(
                    {
                        'user_name': $(this).children('input[name=user]').val(),
                        'user_affiliation': $(this).children('input[name=user_affiliation]').val(),
                        'user_job_title': $(this).children('input[name=user_job_title]').val(),
                    }
                )
            }
        })

        let cols = ['applicant', 'phone', 'address', 'affiliation', 'project_name']
        cols.forEach(function (c) {
            if (!$(`#appilcationForm input[name=${c}]`).val()) {
                checked = false;
            }
        })

        if (!$('#appilcationForm textarea[name=abstract]').val()) {
            checked = false;
        }

        if (checked) {
            $.ajax({
                url: "/submit_sensitive_request",
                data: $('#appilcationForm').serialize() + '&users=' + JSON.stringify(users) + '&csrfmiddlewaretoken=' + $csrf_token +
                    '&' + window.location.search.substring(1),
                type: 'POST',
                dataType: 'json',
            })
                .done(function (result) {
                    alert(gettext('請求已送出，審核完畢後將以Email通知'))
                    window.location.href = `/${$lang}/manager?menu=sensitive`
                })
                .fail(function (xhr, status, errorThrown) {
                    if (xhr.status == 504) {
                        alert(gettext('要求連線逾時'))
                    } else {
                        alert(gettext('發生未知錯誤！請聯絡管理員'))
                    }
                    console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                })
        } else {
            alert(gettext('請完整填寫表格'))
        }
    } else {
        alert(gettext('請先登入'))
    }
}
