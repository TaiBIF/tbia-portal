var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

function changePage(page, menu) {
    $.ajax({
        url: `/change_manager_page?page=${page}&menu=${menu}&lang=${$lang}`,
        type: 'GET',
        success: function (response) {

            // 保留表格 header 修改表格內容
            $(`.${menu}_table tr:not(.${menu}_table_header)`).remove()
            $(`.${menu}_table`).append(`${response.data}`)


            // 修改頁碼
            $(`.${menu}_table`).parent().next('.page_number').remove()

            if (response.total_page > 0){

                $(`.${menu}_table`).parent().after(
                    `<div class="page_number">
                        <a class="num changePage" data-page="1" data-type="${menu}">1</a>
                        <a class="pre"><span></span>${gettext('上一頁')}</a>  
                        <a class="next">${gettext('下一頁')}<span></span></a>
                        <a class="num changePage" data-page="${response.total_page}" data-type="${menu}">${response.total_page}</a>
                        </div>`)

                let html = ''
                for (let i = 0; i < response.page_list.length; i++) {
                    if (response.page_list[i] == response.current_page) {
                        html += ` <a class="num now changePage" data-page="${response.page_list[i]}" data-type="${menu}">${response.page_list[i]}</a>  `;
                    } else {
                        html += ` <a class="num changePage" data-page="${response.page_list[i]}" data-type="${menu}">${response.page_list[i]}</a>  `
                    }
                }

                $(`.${menu} .item .page_number a.pre`).after(html)

                // 如果有下一頁，改掉next的onclick
                if (response.current_page < response.total_page) {
                    $(`.${menu} .item .page_number a.next`).addClass('changePage');
                    $(`.${menu} .item .page_number a.next`).data('page', response.current_page + 1);
                    $(`.${menu} .item .page_number a.next`).data('type', menu);
                } else {
                    $(`.${menu} .item .page_number a.next`).addClass('pt-none')
                }

                // 如果有上一頁，改掉prev的onclick
                if (response.current_page - 1 > 0) {
                    $(`.${menu} .item .page_number a.pre`).addClass('changePage');
                    $(`.${menu} .item .page_number a.pre`).data('page', response.current_page - 1);
                    $(`.${menu} .item .page_number a.pre`).data('type', menu);
                } else {
                    $(`.${menu} .item .page_number a.pre`).addClass('pt-none')
                }

                $('.changePage').off('click')
                $('.changePage').on('click', function () {
                    changePage($(this).data('page'), $(this).data('type'))
                })

                $(".applyARK").on("click", function(){            
                    $(".apply-ark-pop").removeClass('d-none');
                    $(".submit_apply_ark").data('query_id', $(this).data('query_id'));
                });


                $(".addReport").on("click", function(){            

                    $('a.report_file_url').html('')
                    $('a.report_file_url').attr('href','')

                    $(".report-pop").removeClass('d-none');
                    $('input[name=report_query_id]').val($(this).data('query_id'))
                    $('textarea[name=report_content]').val($(this).data('report_content'))
                    if ($(this).data('report_file')){
                        $('a.report_file_url').attr('href', '/media/' + $(this).data('report_file'))
                        $('a.report_file_url').html($(this).data('report_file').replace('sensitive_report/',''))
                    }
                });

            }
        }
    });

}

function withdrawRequest(user_id) {

    $.ajax({
        url: "/withdraw_partner_request",
        data: { 'user_id': user_id, csrfmiddlewaretoken: $csrf_token },
        type: 'POST',
        dataType: 'json',
    })
        .done(function (response) {
            alert(gettext(response.message))
            if (response.message == '申請已撤回') {
                window.location = '/manager'
            }
        })
        .fail(function (xhr, status, errorThrown) {
            alert(gettext('發生未知錯誤！請聯絡管理員'))
            console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })

}

$(document).ready(function () {

    $('.report-pop .send').on('click', function () {

        if (($('textarea[name=report_content]').val()) || ($('input[name=report_file]').val()) ) {

            $.ajax({
                url: "/submit_sensitive_report",
                data: new FormData($('#reportForm').get(0)),
                type: 'POST',
                contentType: false, 
                processData: false,  
              })
                .done(function (response) {
          
                    alert(gettext(response.message))
                    location.reload()
                })
                .fail(function (xhr, status, errorThrown) {
                  alert(gettext('發生未知錯誤！請聯絡管理員'))
                  console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                  $('.report-pop').addClass('d-none')
                })
          
    
        } else {
            alert(gettext('未填入任何成果'))
        }
    })


    $(".hide_apply_ark_pop").on("click", function(){
        $(".apply-ark-pop").addClass("d-none");
    })

    $(".submit_apply_ark").on("click", function(){

            $(".loading_area").removeClass('d-none');

            $(".apply-ark-pop").addClass("d-none");

            $.ajax({
                url: "/submit_apply_ark",
                data: {'query_id': $(this).data('query_id'), csrfmiddlewaretoken: $csrf_token},
                type: 'POST',
                dataType: 'json',
            })
            .done(function (response) {
                alert(gettext(response.message))
                if (response.message.includes('申請完成')) {
                    window.location = '/manager'
                }
                
                $(".loading_area").addClass('d-none');
            })
            .fail(function (xhr, status, errorThrown) {
                alert(gettext('發生未知錯誤！請聯絡管理員'))
                console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)

                $(".loading_area").addClass('d-none');

            })

    })


    //起始 
    changePage(1, 'notification')
    changePage(1, 'download')
    changePage(1, 'download_taxon')
    changePage(1, 'sensitive')

    $(".mb_fixed_btn").on("click", function (event) {
        $(".mbmove").toggleClass("open");
        $(this).toggleClass("now");
    });

    $(".rd_click").on("click", function (event) {
        $(".rd_click").closest("li").removeClass("now");
        $('.rightbox_content').addClass('d-none')
        $(`.rightbox_content.${$(this).data('type')}`).removeClass('d-none')
        $(this).closest("li").toggleClass("now");
        $(this).closest("li").find(".second_menu").slideToggle();
    });

    $(".second_menu a").on("click", function (event) {
        $(this).parent().parent().parent('ul').children('li.now').removeClass("now");
        $(".second_menu a").removeClass("now");
        $(this).addClass("now")
        $(this).parent().parent('li').addClass('now')
    });

    $(`.rd_click[data-type=${$('input[name=menu]').val()}]`).parent().addClass('now')
    $(`.rightbox_content.${$('input[name=menu]').val()}`).removeClass('d-none')

    $('.withdrawRequest').on('click', function () {
        withdrawRequest($(this).data('uid'))
    })

    $('.sendRequest').on('click', function () {
        if ($('input[name=checked-policy]').is(':checked')) {

            $.ajax({
                url: "/send_partner_request",
                data: $('#partnerForm').serialize() + '&user_id=' + $('input[name=user_id]').val(),
                type: 'POST',
                dataType: 'json',
            })
            .done(function (response) {
                alert(gettext(response.message))
                if (response.message == '申請已送出') {
                    window.location = '/manager'
                }
            })
            .fail(function (xhr, status, errorThrown) {
                alert(gettext('發生未知錯誤！請聯絡管理員'))
                console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
            })

        } else {
            alert(gettext('送出前請閱讀並勾選同意保密協議'))
        }
    })

    $('.updateInfo').on('click', function () {
        // remove all notice first
        $('.noticbox').addClass('d-none')

        let checked = true;
        let has_password = false;

        if (!$('#updateForm input[name=name]').val()) { // check name
            $('#updateForm input[name=name]').next('.noticbox').removeClass('d-none')
            checked = false
        }
        // 如果有任何一個跟密碼相關的欄位不是空白才判斷是否正確
        if (!$('#updateForm input[name=now_password]').val() == undefined) {

            if (($('#updateForm input[name=now_password]').val() != '') | ($('#updateForm input[name=new_password]').val() != '') | ($('#updateForm input[name=re_password]').val() != '')) {
                has_password = true
                if (!checkPasswordStr($('#updateForm input[name=now_password]').val())) { // check now password
                    $('#updateForm input[name=now_password]').next('.noticbox').removeClass('d-none')
                    checked = false
                }
                if (!checkPasswordStr($('#updateForm input[name=new_password]').val())) { // check new password
                    $('#updateForm input[name=new_password]').next('.noticbox').removeClass('d-none')
                    checked = false
                }
                if ($('#updateForm input[name=new_password]').val() != $('#updateForm input[name=re_password]').val()) { // check repassword
                    $('#updateForm input[name=re_password]').next('.noticbox').removeClass('d-none')
                    checked = false
                }
            }
        }

        if (checked) {
            $.ajax({
                url: "/update_personal_info",
                data: $('#updateForm').serialize() + '&email=' + $('#updateForm input[name=email]').val() + '&has_password=' + has_password,
                type: 'POST',
                dataType: 'json',
            })
                .done(function (response) {
                    alert(gettext(response.message))
                    if (response.message == '修改完成！請重新登入') {
                        window.location = '/'
                    }
                })
                .fail(function (xhr, status, errorThrown) {
                    alert(gettext('發生未知錯誤！請聯絡管理員'))
                    console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                })
        }
    })

})