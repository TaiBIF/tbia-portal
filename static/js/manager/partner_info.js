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

function showRequest(query_id, query, sdr_id) {
    $.ajax({
        url: "/get_request_detail?query_id=" + query_id + '&sdr_id=' + sdr_id,
        type: 'GET',
    })
        .done(function (response) {

            // console.log(response)

            $('.detail-pop .send-check').removeClass('d-none')
            $('.detail-pop .send-submitted').addClass('d-none')

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

            if (response.detail.is_agreed_report == true) {
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

            // 審查意見

            if (response.review.status != 'pending') {
                $('#reviewForm input[name=reviewer_name]').val(response.review.reviewer_name)
                $('#reviewForm textarea[name=comment]').val(response.review.comment)
                $('#reviewForm select[name=status]').val(response.review.status)
                $('#reviewForm input[name=reviewer_name]').attr('disabled', 'disabled');
                $('#reviewForm textarea[name=comment]').attr('disabled', 'disabled');
                $('#reviewForm select[name=status]').attr('disabled', 'disabled');

                $('.detail-pop .send-check').addClass('d-none')
                $('.detail-pop .send-submitted').removeClass('d-none')
            } else {
                $('#reviewForm input[name=reviewer_name]').attr('disabled', false);
                $('#reviewForm textarea[name=comment]').attr('disabled', false);
                $('#reviewForm select[name=status]').attr('disabled', false);
            }

        })
        .fail(function (xhr, status, errorThrown) {
            alert(gettext('發生未知錯誤！請聯絡管理員'))
            console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })

}

function changePage(page, menu) {
    $.ajax({
        url: `/change_manager_page?page=${page}&menu=${menu}&from=partner`,
        type: 'GET',
        success: function (response) {

            console.log(response.data);

            // 保留表格 header 修改表格內容
            $(`.${menu}_table tr:not(.${menu}_table_header)`).remove()
            $(`.${menu}_table`).append(`${response.data}`)

            // 修改頁碼
            $(`.${menu}_table`).parent().next('.page_number').remove()
            //if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕

            if (response.total_page > 0) {

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

                // let menu = 'sensitive_apply'

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

                $('.save_btn').off('click')
                $('.save_btn').on('click', function () {
                    update_user_status($(this).data('id'))
                })

                $('.showRequest').off('click')
                $('.showRequest').on('click', function () {
                    let query_id = $(this).data('query_id');
                    let query = $(this).data('query');
                    let sdr_id = $(this).data('sdr_id');
                    showRequest(query_id, query, sdr_id)
                })
            }
        }
    });

}

$(document).ready(function () {

    $('.downloadReport').on('click', function () {
        $('#downloadReport').submit()
    })

    $('.downloadPartnerReport').on('click', function () {
        $('#downloadPartnerReport').submit()
    })

    // 起始頁面
    changePage(1, 'account')
    changePage(1, 'sensitive_apply')

    $('.changeMenu').on('click', function () {
        let menu = $(this).data('menu');
        $('.rightbox_content').addClass('d-none');
        $(`.rightbox_content.${menu}`).removeClass('d-none');
        changeURL(menu)
    })

    $('.hide_submit-check').on('click', function () {
        $('.submit-check').addClass('d-none')
    })

    // $('.updateFeedback').on('click', function () {
    //     let current_id = $(this).data('fid');
    //     $.ajax({
    //         url: "/update_feedback",
    //         data: {
    //             'current_id': current_id,
    //             'csrfmiddlewaretoken': $csrf_token,
    //         },
    //         type: 'POST',
    //         dataType: 'json',
    //     })
    //         .done(function (response) {
    //             alert('修改完成')
    //             window.location.reload()
    //         })
    //         .fail(function (xhr, status, errorThrown) {
    //             alert(gettext('發生未知錯誤！請聯絡管理員'))

    //             console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
    //         })
    // })



    $('.showRequest').on('click', function () {
        let query_id = $(this).data('query_id');
        let query = $(this).data('query');
        let sdr_id = $(this).data('sdr_id');
        showRequest(query_id, query, sdr_id)
    })

    $('.updateInfo').on('click', function () {
        // remove all notice first
        $('.noticbox').addClass('d-none')
        let checked = true;
        // 這邊的判斷不能直接用input -> 加上forloop counter?
        /*if (!$('input[name=link]').val()){ 
            $('input[name=link]').next('.noticbox').css('display','')
            checked = false
        }  
        if (!$('input[name=description]').val()){ 
            $('input[name=description]').next('.noticbox').css('display','')
            checked = false
        }  */
        if (checked) {
            $.ajax({
                url: "/update_partner_info",
                data: $('#updateForm').serialize(),
                type: 'POST',
                dataType: 'json',
            })
                .done(function (response) {
                    alert(gettext(response.message))
                    if (response.message == '修改完成！') {
                        window.location = '/'
                    }
                })
                .fail(function (xhr, status, errorThrown) {
                    alert(gettext('發生未知錯誤！請聯絡管理員'))

                    console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
                })
        }
    })

    $('.changePage').on('click', function () {
        changePage($(this).data('page'), $(this).data('type'))
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
            $(this).next('.panel').removeClass('d-block').addClass('d-none')
        } else {
            $('.accordion').not(this).removeClass('active')
            $('.accordion').not(this).next('.panel').removeClass('d-block').addClass('d-none')
            $(this).addClass('active')
            $(this).next('.panel').addClass('d-block').removeClass('d-none')
        }
    })

    $('.save_btn').on('click', function () {
        update_user_status($(this).data('id'))
    })

    $(`a.${$('input[name=menu]').val()}`).addClass('now')
    $(`a.${$('input[name=menu]').val()}`).parent(".second_menu").slideToggle();
    $(`.rightbox_content.${$('input[name=menu]').val()}`).removeClass('d-none')
})

function update_user_status(current_id) {
    $.ajax({
        url: "/update_user_status",
        data: {
            'user_id': current_id,
            'csrfmiddlewaretoken': $csrf_token,
            'role': $('select[name=role]').find(':selected').val(),
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
