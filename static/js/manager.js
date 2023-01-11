var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

function changePage(page, menu){
    $.ajax({
        url: `/change_manager_page?page=${page}&menu=${menu}`,
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
                $('.pre').addClass('changePage');
                $('.pre').data('page', response.current_page-1);
                $('.pre').data('type', menu);    
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
                $('.next').addClass('changePage');
                $('.next').data('page', response.current_page+1);
                $('.next').data('type', menu);
            } else {
                $('.next').addClass('pt-none')
            }

            $('.changePage').on('click', function(){
                changePage($(this).data('page'),$(this).data('type'))
            })        
                
        }
    });

}

function withdrawRequest(user_id){

    $.ajax({
        url: "/withdraw_partner_request",
        data: {'user_id': user_id,csrfmiddlewaretoken: $csrf_token},
        type: 'POST',
        dataType : 'json',
    })
    .done(function(response) {
        alert(response.message)
        if (response.message=='申請已撤回'){
            window.location = '/manager'
        }
    })
    .fail(function( xhr, status, errorThrown ) {
        alert('發生未知錯誤！請聯絡管理員')
        console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
    })  

}

$(document).ready(function () {

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

    $('.changePage').on('click', function(){
        changePage($(this).data('page'),$(this).data('type'))
    })

    $(`.rd_click[data-type=${$('input[name=menu]').val()}]`).parent().addClass('now')
    $(`.rightbox_content.${$('input[name=menu]').val()}`).removeClass('d-none')

    $('.withdrawRequest').on('click', function(){
        withdrawRequest($(this).data('uid'))
    })

    $('.sendRequest').on('click', function(){
        if ($('input[name=checked-policy]').is(':checked')) {

            $.ajax({
                url: "/send_partner_request",
                data: $('#partnerForm').serialize() + '&user_id=' + $('input[name=user_id]').val(),
                type: 'POST',
                dataType : 'json',
            })
            .done(function(response) {
                alert(response.message)
                if (response.message=='申請已送出'){
                    window.location = '/manager'
                }
            })
            .fail(function( xhr, status, errorThrown ) {
                alert('發生未知錯誤！請聯絡管理員')
                console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
            })  
            
        } else {
            alert('送出前請閱讀並勾選同意保密協議')
        }    
    })

    $('.updateInfo').on('click', function(){
        // remove all notice first
        $('.noticbox').addClass('d-none')
    
        let checked = true;
        let has_password = false;
    
        if (!$('#updateForm input[name=name]').val()){ // check name
            $('#updateForm input[name=name]').next('.noticbox').removeClass('d-none')
            checked = false
        }  
        // 如果有任何一個跟密碼相關的欄位不是空白才判斷是否正確
        if (($('#updateForm input[name=now_password]').val()!='')|($('#updateForm input[name=new_password]').val()!='')|($('#updateForm input[name=re_password]').val()!='')){
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
    
        if (checked){
            $.ajax({
                url: "/update_personal_info",
                data: $('#updateForm').serialize() + '&email=' + $('#updateForm input[name=user_email]').val() + '&has_password=' + has_password,
                type: 'POST',
                dataType : 'json',
            })
            .done(function(response) {
                alert(response.message)
                if (response.message=='修改完成！請重新登入'){
                    window.location = '/'
                }
            })
            .fail(function( xhr, status, errorThrown ) {
                alert('發生未知錯誤！請聯絡管理員')
                console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
            })  
        }
    }) 

})

