var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

function changeURL(menu) {
    history.pushState(null, '', window.location.pathname + '?' + 'menu=' + menu);
}

// 如果按上下一頁
window.onpopstate = function (e) {
    e.preventDefault();

    $('.rightbox_content').addClass('d-none')
    $('.col_menu.second_menu a').removeClass('now')
    $('.col_menu.second_menu').addClass('d-none')

    let queryString = window.location.search;
    let urlParams = new URLSearchParams(queryString);

    let menu = urlParams.get('menu')
    if (menu) {

        $(`a.${menu}`).addClass('now')
        $(`a.${menu}`).parent(".second_menu").slideToggle();

        $(`.rightbox_content.${menu}`).removeClass('d-none')
    }
};


function changePage(page, menu) {
    $.ajax({
        url: `/change_manager_page?page=${page}&menu=${menu}`,
        type: 'GET',
        success: function (response) {

            // 保留表格 header 修改表格內容
            $(`.${menu}_table tr:not(.${menu}_table_header)`).remove()
            $(`.${menu}_table`).append(`${response.data}`)
            
            $(`.${menu}_table`).parent().next('.page_number').remove()

            // 修改頁碼

            if (response.total_page > 0){
                //if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕
                $(`.${menu}_table`).parent().after(
                    `<div class="page_number">
                    <a class="num changePage" data-page="1" data-type="${menu}">1</a>
                    <a class="pre"><span></span>上一頁</a>  
                    <a class="next">下一頁<span></span></a>
                    <a class="num changePage" data-page="${response.total_page}" data-type="${menu}">${response.total_page}</a>
                    </div>`)
                //}		

                // if (menu == 'sensitive_apply') {
                //     menu = 'sensitive'
                // } else {
                //     menu = menu
                // }


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

                $('.saveStatus').off('click')
                $('.saveStatus').on('click', function () {
                    let current_id = $(this).data('pmid')
                    saveStatus(current_id)
                })

                $('.showRequest').off('click')
                $('.showRequest').on('click', function () {
                    let query_id = $(this).data('query_id')
                    let query = $(this).data('query')
                    let sdr_id = $(this).data('sdr_id')
                    let is_transferred = $(this).data('is_transferred')
                    showRequest(query_id, query, sdr_id, is_transferred)
                })

                $('select[name=is_replied]').off('change')
                $('select[name=is_replied]').on('change', function () {
                    let current_id = $(this).data('fid')
                    updateFeedback(current_id)
                })
            }
        }
    });

}



$(document).ready(function () {

    $('.downloadReport').on('click', function(){
        $(this).children('form').submit()
    })

    // 起始頁面
    changePage(1, 'feedback')
    changePage(1, 'account')
    changePage(1, 'sensitive_apply')
    changePage(1, 'sensitive_track')

    $(`a.${$('input[name=menu]').val()}`).addClass('now')
    $(`a.${$('input[name=menu]').val()}`).parent(".second_menu").slideToggle();

    $(`.rightbox_content.${$('input[name=menu]').val()}`).removeClass('d-none')

    $('.updateFeedback').on('click', function () {
        let current_id = $(this).data('fid')
        updateFeedback(current_id)
    })

    $('.saveStatus').on('click', function () {
        let current_id = $(this).data('pmid')
        saveStatus(current_id)
    })

    $('.hide_submit-check').on('click', function () {
        $('.submit-check').addClass('d-none')
    })

    $('.hide_submit-transfer').on('click', function () {
        $('.submit-transfer').addClass('d-none')
    })

    $('.hide_submit-partial-transfer').on('click', function () {
        $('.partial-pop').addClass('d-none')
    })

    $('.updateInfo').on('click', function () {
        // remove all notice first
        $('.noticbox').addClass('d-none')

        let checked = true;

        if (!$('textarea[name=about_content]').val()) { // check name
            $('textarea[name=about_content]').next('.noticbox').removeClass('d-none')
            checked = false
        }

        if (checked) {
            $.ajax({
                url: "/update_tbia_about",
                data: $('#updateForm').serialize(),
                type: 'POST',
                dataType: 'json',
            })
                .done(function (response) {
                    alert('修改完成')
                })
                .fail(function (xhr, status, errorThrown) {
                    alert(gettext('發生未知錯誤！請聯絡管理員'))

                    console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                })
        }
    })

    $(".mb_fixed_btn").on("click", function (event) {
        $(".mbmove").toggleClass("open");
        $(this).toggleClass("now");
    });

    $(".rd_click").on("click", function (event) {
        $(".rd_click").closest("li").removeClass("now");
        $(this).closest("li").toggleClass("now");
        $(this).closest("li").find(".second_menu").slideToggle();
    });

    $(".second_menu a").on("click", function (event) {
        $(this).parent().parent().parent('ul').children('li.now').removeClass("now");
        $(".second_menu a").removeClass("now");
        $(this).addClass("now")
        $(this).parent().parent('li').addClass('now')
    });

    $('.showRequest').on('click', function () {
        let query_id = $(this).data('query_id')
        let query = $(this).data('query')
        let sdr_id = $(this).data('sdr_id')
        let is_transferred = $(this).data('is_transferred')
        showRequest(query_id, query, sdr_id, is_transferred)
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

    $('.open-page').on('click', function () {
        window.location = $(this).data('href')
    })


    $('.changeMenu').on('click', function () {
        let menu = $(this).data('menu');
        $('.rightbox_content').addClass('d-none');
        $(`.rightbox_content.${menu}`).removeClass('d-none');
        changeURL(menu)
    })

    $('.changePage').on('click', function () {
        changePage($(this).data('page'), $(this).data('type'))
    })

    $('.send-transfer').on('click', function () {
        $('.submit-transfer').removeClass('d-none')
    })


    $('.send-partial-transfer').on('click', function () {

        // $.ajax({
        //     url: "/get_partial_partner?query_id" + $('form#reviewForm input[name=query_id]').val(),
        //     type: 'GET',
        //     // data: $('#reviewForm').serialize() + '&csrfmiddlewaretoken=' + $csrf_token,
        //     // dataType: 'json'
        // })
        //     .done(function (response) {
        //         // alert('送出成功')
        //         // window.location.reload()
        //         for (p of response){
        //             $('#partial-partner-select').html(``)
        //         }

                $('.partial-pop').removeClass('d-none')
            // })
            // .fail(function (xhr, status, errorThrown) {
            //     alert(gettext('發生未知錯誤！請聯絡管理員'))

            //     console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
            // })


    })

    $('.send-check').on('click', function () {

        let checked = true;

        if ((!$(`#reviewForm input[name=reviewer_name]`).val()) | (!$(`#reviewForm textarea[name=comment]`).val())) {
            checked = false;
        }

        if (checked) {
            $('.submit-check').removeClass('d-none')

        } else {
            alert('請完整填寫審查意見表格')
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

    $('.accordion').on('click', function () {
        if ($(this).hasClass('active')) {
            $(this).removeClass('active')
            $(this).next('.panel').addClass('d-none').removeClass('d-block')
        } else {
            // 
            $('.accordion').not(this).removeClass('active')
            $('.accordion').not(this).next('.panel').addClass('d-none').removeClass('d-block')
            $(this).addClass('active')
            $(this).next('.panel').removeClass('d-none').addClass('d-block')
        }
    })

})


function saveStatus(current_id) {
    $.ajax({
        url: "/update_user_status",
        data: {
            'user_id': current_id,
            csrfmiddlewaretoken: $csrf_token,
            'role': $(`select[name="role"][data-id=${current_id}]`).val(),
            'status': $(`select[name="status"][data-id=${current_id}]`).val(),
        },
        type: 'POST',
        dataType: 'json',
    })
        .done(function (response) {
            if (response['exceed_ten']) {
                alert('修改失敗！每單位最多只能有10個狀態為通過的帳號')
                location.reload()
            } else {
                alert('修改完成')
            }
        })
        .fail(function (xhr, status, errorThrown) {
            alert(gettext('發生未知錯誤！請聯絡管理員'))

            console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })
}

function showRequest(query_id, query, sdr_id, is_transferred) {

    $.ajax({
        url: "/get_request_detail?query_id=" + query_id + '&sdr_id=' + sdr_id,
        type: 'GET',
    })
        .done(function (response) {

            // console.log(response.partners)
            // 如果沒有sdr_id的話 只顯示申請詳細資訊
            $('.detail-pop .resp-box').removeClass('d-none')
            $('.detail-pop [class^="send-"]').removeClass('d-none')


            $('.detail-pop .send-check, .detail-pop .send-transfer').removeClass('d-none')
            $('.detail-pop .send-submitted, .detail-pop .send-transferred').addClass('d-none')
            $('.detail-pop .send-submitted, .detail-pop .send-partial-transferred').addClass('d-none')

            // 要先全部重設
            $("#detailForm").trigger("reset");
            $("#reviewForm").trigger("reset");

            $('#reviewForm input[name=query_id] ').val(query_id)
            $('#reviewForm input[name=sdr_id] ').val(sdr_id)

            $('.detail-pop').removeClass('d-none')
            $('.detail-pop .riginf').html(query)
            $('.detail-pop input[name=applicant] ').val(response.detail.applicant)
            $('.detail-pop input[name=applicant_email] ').val(response.detail.applicant_email)
            $('.detail-pop input[name=phone] ').val(response.detail.phone)
            $('.detail-pop input[name=address] ').val(response.detail.address)
            $('.detail-pop input[name=affiliation] ').val(response.detail.affiliation)
            $('.detail-pop input[name=job_title] ').val(response.detail.job_title)
            $('.detail-pop input[name=project_name] ').val(response.detail.project_name)
            $('.detail-pop textarea[name=abstract] ').val(response.detail.abstract)
            
            if (response.detail.is_agreed_report==true){
                $('.detail-pop input[name=is_agreed_report]').prop('checked', true);
            }


            if (response.detail.type == '0') {
                $('.detail-pop input[name=type] ').val('個人研究計畫')
                $('.project_type').html('個人研究計畫名稱')
                $('.p_affli').addClass('d-none')
                $('.p_principal').addClass('d-none')
            } else {
                $('.detail-pop input[name=type] ').val('委辦工作計畫')
                $('.project_type').html('委辦工作計畫名稱')
                $('.p_affli').removeClass('d-none')
                $('.p_principal').removeClass('d-none')
                $('.detail-pop input[name=project_affiliation] ').val(response.detail.project_affiliation)
                $('.detail-pop input[name=principal_investigator] ').val(response.detail.principal_investigator)
            }

            $('.apply_peo .item_set1').remove()
            if (response.detail.users.length > 0) {
                for (let i = 0; i < response.detail.users.length; i++) {
                    $('.apply_peo').append(`
                    <div class="item_set1">
                        <span class="ml-10px">姓名</span>
                        <input type="text" value="${response.detail.users[i]['user_name']}" disabled>
                        <span class="ml-10px">單位</span>
                        <input type="text" value="${response.detail.users[i]['user_affiliation']}" disabled>
                        <span class="ml-10px">職稱</span>
                        <input type="text" name="user_job_title" value="${response.detail.users[i]['user_job_title']}" disabled>
                    </div>`)
                }
            } else {
                $('.apply_peo').append('<div class="item_set1 bg-transparent">無</div>')
            }


            // partial
            // 如果完全沒有partner的話 disable 部分轉交的按鈕
            
            $('#partial-partner-select').html('')

            if (response.partners.length > 0){
                
                for (p of response.partners){
                    $('#partial-partner-select').append(`<option value="${p.id}">${p.select_title}</option>`)
                }

                if (response.already_transfer_partners.length > 0){
                    $('#already_transfer_partners').html(`*已轉交單位：${response.already_transfer_partners.join('、')}`)
                } else {
                    $('#already_transfer_partners').html('')
                }

            } else {

                if (response.has_partial_transferred == true){
                    $('.send-transferred').removeClass('d-none')
                    $('.send-partial-transfer').addClass('d-none')
                }

                
            }

            
            if (sdr_id != ''){

                // 審查意見
                if (is_transferred == 'True') {
                    $('.detail-pop .send-check, .detail-pop .send-transfer, .detail-pop .send-submitted, .detail-pop .send-partial-transfer').addClass('d-none')
                    $('.send-transferred').removeClass('d-none')
                } else if (response.review.status != 'pending') {
                    $('#reviewForm input[name=reviewer_name]').val(response.review.reviewer_name)
                    $('#reviewForm textarea[name=comment]').val(response.review.comment)
                    $('#reviewForm select[name=status]').val(response.review.status)
                    $('#reviewForm input[name=reviewer_name]').attr('disabled', 'disabled');
                    $('#reviewForm textarea[name=comment]').attr('disabled', 'disabled');
                    $('#reviewForm select[name=status]').attr('disabled', 'disabled');

                    $('.detail-pop .send-check, .detail-pop .send-transfer, .detail-pop .send-transferred, .detail-pop .send-partial-transfer').addClass('d-none')
                    $('.detail-pop .send-submitted').removeClass('d-none')
                } else {
                    $('#reviewForm input[name=reviewer_name]').attr('disabled', false);
                    $('#reviewForm textarea[name=comment]').attr('disabled', false);
                    $('#reviewForm select[name=status]').attr('disabled', false);
                }
            } else {
                $('.detail-pop .resp-box').addClass('d-none')
                $('.detail-pop [class^="send-"]').addClass('d-none')
            }

        })
        .fail(function (xhr, status, errorThrown) {
            alert(gettext('發生未知錯誤！請聯絡管理員'))

            console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })

}

function updateFeedback(current_id) {
    $.ajax({
        url: "/update_feedback",
        data: {
            'current_id': current_id,
            csrfmiddlewaretoken: $csrf_token,
        },
        type: 'POST',
        dataType: 'json',
    })
        .done(function (response) {
            alert('修改完成')
            window.location.reload()
        })
        .fail(function (xhr, status, errorThrown) {
            alert(gettext('發生未知錯誤！請聯絡管理員'))

            console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })
}