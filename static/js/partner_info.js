var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

function changeURL(menu){
    history.pushState(null, '', window.location.pathname + '?'  + 'menu=' + menu);
}

// 如果按上下一頁
window.onpopstate = function(e) {
    e.preventDefault(); 

    $('.rightbox_content').addClass('d-none')
    $('.col_menu.second_menu a').removeClass('now')
    $('.col_menu.second_menu').addClass('d-none')

    let queryString = window.location.search;
    let urlParams = new URLSearchParams(queryString);

    let menu = urlParams.get('menu')
    if (menu){
        $(`a.${ menu }`).addClass('now')
        $(`a.${ menu }`).parent(".second_menu").slideToggle();
        $(`.rightbox_content.${ menu }`).removeClass('d-none')
    }
};

function changePage(page, menu){
    $.ajax({
        url: `/change_manager_page?page=${page}&menu=${menu}&from=partner`,
        type: 'GET',
        success: function(response){
            // 修改表格內容
            $(`.${menu}_table`).html(`
                ${response.header}
                ${response.data}`)
            $(`.${menu}_table`).parent().next('.page_number').remove()

            // 修改頁碼
            if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕
                $(`.${menu}_table`).parent().after(
                    `<div class="page_number">
                    <a href="javascript:;" class="num changePage" data-page="1" data-type="${menu}">1</a>
                    <a href="javascript:;" class="pre">上一頁</a>  
                    <a href="javascript:;" class="next">下一頁</a>
                    <a href="javascript:;" class="num changePage" data-page="${response.total_page}" data-type="${menu}">${response.total_page}</a>
                    </div>`)
            }		
                
            if (response.page_list.includes(response.current_page-1)){
                $('.pre').addClass('changePage')
                $('.pre').data('page', response.current_page-1)
                $('.pre').data('type', menu)
            } else {
                $('.pre').addClass('pt-none')
            }

            let html = ''
            for (let i = 0; i < response.page_list.length; i++) {
                if (response.page_list[i] == response.current_page){
                    html += ` <a href="javascript:;" class="num now changePage" data-page="${response.page_list[i]}" data-type="${menu}">${response.page_list[i]}</a>  `;
                } else {
                    html += ` <a href="javascript:;" class="num changePage" data-page="${response.page_list[i]}" data-type="${menu}">${response.page_list[i]}</a>  `
                }
            }

            $('.pre').after(html)
    
            // 如果有下一頁，改掉next的onclick
            if (response.current_page < response.total_page){
                $('.next').addClass('changePage')
                $('.next').data('page', response.current_page+1)
                $('.next').data('type', menu)
            } else {
                $('.next').addClass('pt-none')
            } 

            $('.changePage').on('click', function(){
                changePage($(this).data('page'),$(this).data('type'))
            })        
        }
    });

}

$(document).ready(function () {

    $('.changeMenu').on('click', function(){
        let menu = $(this).data('menu');
        $('.rightbox_content').addClass('d-none'); 
        $(`.rightbox_content.${menu}`).removeClass('d-none'); 
        changeURL(menu)
    })

    $('.hide_submit-check').on('click', function(){
        $('.submit-check').addClass('d-none')
    })

    $('.updateFeedback').on('click', function(){
        let current_id = $(this).data('fid');
        $.ajax({
            url: "/update_feedback",
            data: {
                'current_id': current_id,
                'csrfmiddlewaretoken': $csrf_token,
            },
            type: 'POST',
            dataType : 'json',
        })
        .done(function(response) {
            alert('修改完成')
            window.location.reload()
        })
        .fail(function( xhr, status, errorThrown ) {
            alert('發生未知錯誤！請聯絡管理員')
            console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
        })  
    })

    $('.showRequest').on('click',function(){
        let query_id = $(this).data('query_id');
        let query = $(this).data('query');
        let sdr_id = $(this).data('sdr_id');

        $.ajax({
            url: "/get_request_detail?query_id=" + query_id + '&sdr_id=' + sdr_id,
            type: 'GET',
        })
        .done(function(response) {
    
            $('.detail-pop .send-check').removeClass('d-none')
            $('.detail-pop .send-submitted').addClass('d-none')
    
            // 要先全部清除
            $("#detailForm").trigger("reset");
            $("#reviewForm").trigger("reset");
    
            $('#reviewForm input[name=query_id] ').val(query_id)
            $('#reviewForm input[name=sdr_id] ').val(sdr_id)
    
            $('.detail-pop').removeClass('d-none')
            $('.detail-pop .riginf').html(query)
            $('.detail-pop input[name=applicant] ').val(response.detail.applicant)
            $('.detail-pop input[name=phone] ').val(response.detail.phone)
            $('.detail-pop input[name=address] ').val(response.detail.address)
            $('.detail-pop input[name=affiliation] ').val(response.detail.affiliation)
            $('.detail-pop input[name=project_name] ').val(response.detail.project_name)
            $('.detail-pop textarea[name=abstract] ').val(response.detail.abstract)
    
            if (response.detail.type=='0'){
                $('.detail-pop input[name=type] ').val('個人研究計畫')
                $('.project_type').html('個人研究計畫名稱')
                $('.p_affli').addClass('d-none')
            } else {
                $('.detail-pop input[name=type] ').val('委辦工作計畫')
                $('.project_type').html('委辦工作計畫名稱')
                $('.p_affli').removeClass('d-none')
                $('.detail-pop input[name=project_affiliation] ').val(response.detail.project_affiliation)
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
        .fail(function( xhr, status, errorThrown ) {
            alert('發生未知錯誤！請聯絡管理員')
            console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
        })  
    })

    $('.updateInfo').on('click', function(){
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
        if (checked){
            $.ajax({
                url: "/update_partner_info",
                data: $('#updateForm').serialize(),
                type: 'POST',
                dataType : 'json',
            })
            .done(function(response) {
                alert(response.message)
                if (response.message=='修改完成！'){
                    window.location = '/'
                }
            })
            .fail(function( xhr, status, errorThrown ) {
                alert('發生未知錯誤！請聯絡管理員')
                console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
            })  
        }
    })

    $('.changePage').on('click', function(){
        changePage($(this).data('page'),$(this).data('type'))
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
    
    $('.send-check').on('click',function(){
        let checked = true;

        if ((!$(`input[name=reviewer_name]`).val())|(!$(`textarea[name=comment]`).val())){
            checked = false;
        }

        if (checked) {
            $('.submit-check').removeClass('d-none')
        } else {
            alert('請完整填寫審查意見表格')
        }
    })

    $('.send_review').on('click', function (){
        $.ajax({
            url: "/submit_sensitive_response",
            type: 'POST',
            data: $('#reviewForm').serialize() + '&csrfmiddlewaretoken=' + $csrf_token,
            dataType: 'json'
        })
        .done(function(response) {
            alert('送出成功')
            window.location.reload()
        })
        .fail(function( xhr, status, errorThrown ) {
            alert('發生未知錯誤！請聯絡管理員')
            console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
        })  
    })

    $('.accordion').on('click', function(){
        if ($(this).hasClass('active')){
            $(this).removeClass('active')
            $(this).next('.panel').removeClass('d-block').addClass('d-none')
        } else {
            // 
            $('.accordion').not(this).removeClass('active')
            $('.accordion').not(this).next('.panel').removeClass('d-block').addClass('d-none')
            $(this).addClass('active')
            $(this).next('.panel').addClass('d-block').removeClass('d-none')
        }
    })

    $('.save_btn').on('click',function(){
        let current_id = $(this).data('id')
        $.ajax({
            url: "/update_user_status",
            data: {'user_id': current_id,
                    'csrfmiddlewaretoken': $csrf_token,
                    'role': $('select[name=role]').find(':selected').val(),
                    'status': $(`select[name="status"][data-id=${current_id}]`).val(),
                },
            type: 'POST',
            dataType : 'json',
        })
        .done(function(response) {
            alert('修改完成')                
        })
        .fail(function( xhr, status, errorThrown ) {
            alert('發生未知錯誤！請聯絡管理員')
            console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
        })  
    })

    $(`a.${ $('input[name=menu]').val() }`).addClass('now')
    $(`a.${ $('input[name=menu]').val() }`).parent(".second_menu").slideToggle();
    $(`.rightbox_content.${ $('input[name=menu]').val() }`).removeClass('d-none')
})