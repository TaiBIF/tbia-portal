var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");


$(function () {

    $('.sendRequest').on('click', function () {
        sendRequest()
    })

    $('#appilcationForm .inpu_3 .input_item select[name=type]').on('change', function () {
        if ($('#appilcationForm .inpu_3 .input_item select[name=type]').val() == '1') {
            $('.p_affli').removeClass('d-none')
            $('.p_principal').removeClass('d-none')
            $('.project_type').html(`<span class="color_red">*</span>${gettext('委辦工作計畫名稱')}`)
        } else {
            $('.p_affli').addClass('d-none')
            $('.p_principal').addClass('d-none')
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
    if ($('input[name=is_authenticated]').val() == 'True') {
        let checked = true;

        let users = [];
        $('.apply_peo .item_set1').each(function () {
            if ( // 如果不是全空才加上去
                !((!$(this).children('input[name=user]').val()) & (!$(this).children('input[name=user_affiliation]').val()) & (!$(this).children('input[name=user_job_title]').val()))
            ) {
                users.push({
                    'user_name': $(this).children('input[name=user]').val(),
                    'user_affiliation': $(this).children('input[name=user_affiliation]').val(),
                    'user_job_title': $(this).children('input[name=user_job_title]').val(),
                })
            }
        })

        // 這邊要依據 是個人計畫還是委辦工作計畫 來判斷必填欄位有哪些
        let cols = ['applicant', 'phone', 'address', 'affiliation', 'job_title', 'project_name', 'research_proposal']
        cols.forEach(function (c) {
            if (!$(`#appilcationForm input[name=${c}]`).val()) {
                checked = false;
            }
        })

        if ($('#appilcationForm .inpu_3 .input_item select[name=type]').val() == '1') {
            c = 'principal_investigator';
            if (!$(`#appilcationForm input[name=${c}]`).val()) {
                checked = false;
            }
        }

        if (!$('#appilcationForm textarea[name=abstract]').val()) {
            checked = false;
        }

        let is_agreed_report = 'f';
        if ($('input[name=is_agreed_report]').is(':checked')) {
            is_agreed_report = 't'
        } 

        if (checked) {
            // 使用 FormData 來處理檔案上傳
            let formData = new FormData();
            
            // 添加表單的所有欄位
            $('#appilcationForm').serializeArray().forEach(function(field) {
                formData.append(field.name, field.value);
            });
            
            // 添加其他必要的資料
            formData.append('is_agreed_report', is_agreed_report);
            formData.append('users', JSON.stringify(users));
            formData.append('csrfmiddlewaretoken', $csrf_token);
            
            // 添加 URL 參數
            let urlParams = new URLSearchParams(window.location.search);
            urlParams.forEach(function(value, key) {
                formData.append(key, value);
            });
            
            // 添加檔案
            // 假設你的檔案輸入框的 name 是 'uploaded_files'
            let fileInput = $('input[type="file"][name="uploaded_files"]')[0];
            if (fileInput && fileInput.files.length > 0) {
                // 如果支援多檔案上傳
                for (let i = 0; i < fileInput.files.length; i++) {
                    formData.append('uploaded_files', fileInput.files[i]);
                }
            }
            
            // 或者如果你有多個不同的檔案輸入框
            $('input[type="file"]').each(function() {
                let input = this;
                if (input.files.length > 0) {
                    for (let i = 0; i < input.files.length; i++) {
                        formData.append(input.name, input.files[i]);
                    }
                }
            });

            $.ajax({
                url: "/submit_sensitive_request",
                data: formData,
                type: 'POST',
                dataType: 'json',
                processData: false, 
                contentType: false, 
                enctype: 'multipart/form-data' 
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

// function sendRequest() {

//     if ($('input[name=is_authenticated]').val() == 'True') {

//         let checked = true;

//         let users = [];
//         $('.apply_peo .item_set1').each(function () {
//             if ( // 如果不是全空才加上去
//                 !((!$(this).children('input[name=user]').val()) & (!$(this).children('input[name=user_affiliation]').val()) & (!$(this).children('input[name=user_job_title]').val()))
//             ) {
//                 users.push(
//                     {
//                         'user_name': $(this).children('input[name=user]').val(),
//                         'user_affiliation': $(this).children('input[name=user_affiliation]').val(),
//                         'user_job_title': $(this).children('input[name=user_job_title]').val(),
//                     }
//                 )
//             }
//         })

//         // 這邊要依據 是個人計畫還是委辦工作計畫 來判斷必填欄位有哪些
//         let cols = ['applicant', 'phone', 'address', 'affiliation', 'job_title', 'project_name', 'research_proposal']
//         cols.forEach(function (c) {
//             if (!$(`#appilcationForm input[name=${c}]`).val()) {
//                 checked = false;
//             }
//         })

//         if ($('#appilcationForm .inpu_3 .input_item select[name=type]').val() == '1') {

//             c = 'principal_investigator';

//             if (!$(`#appilcationForm input[name=${c}]`).val()) {
//                 checked = false;
//             }

//         }
        

//         if (!$('#appilcationForm textarea[name=abstract]').val()) {
//             checked = false;
//         }

//         let is_agreed_report = 'f';

//         if ($('input[name=is_agreed_report]').is(':checked')) {
//             is_agreed_report = 't'
//         } 

//         if (checked) {
//             $.ajax({
//                 url: "/submit_sensitive_request",
//                 data: $('#appilcationForm').serialize() + '&is_agreed_report=' + is_agreed_report + '&users=' + JSON.stringify(users) + '&csrfmiddlewaretoken=' + $csrf_token +
//                     '&' + window.location.search.substring(1),
//                 type: 'POST',
//                 dataType: 'json',
//             })
//             .done(function (result) {
//                 alert(gettext('請求已送出，審核完畢後將以Email通知'))
//                 window.location.href = `/${$lang}/manager?menu=sensitive`
//             })
//             .fail(function (xhr, status, errorThrown) {
//                 if (xhr.status == 504) {
//                     alert(gettext('要求連線逾時'))
//                 } else {
//                     alert(gettext('發生未知錯誤！請聯絡管理員'))
//                 }
//                 console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
//             })
//         } else {
//             alert(gettext('請完整填寫表格'))
//         }
//     } else {
//         alert(gettext('請先登入'))
//     }
// }