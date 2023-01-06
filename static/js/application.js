var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");


$( function() {

    $('.sendRequest').on('click', function(){
        sendRequest()
    })

    $('.inpu_2 .input_item select[name=type]').on('change', function(){
        if ($('.inpu_2 .input_item select[name=type]').val()=='1'){
            $('.p_affli').removeClass('d-none')
            $('.project_type').html('<span class="color_red">*</span>委辦工作計畫名稱')
        } else {
            $('.p_affli').addClass('d-none')
            $('.project_type').html('<span class="color_red">*</span>個人研究計畫名稱')

        }
    })

    $('.item_set1 .add').on('click', function(){
        $('.apply_peo').append(`
        <div class="item_set1">
            <input type="text" name="user" placeholder="姓名">
            <input type="text" name="user_affiliation" placeholder="單位">
            <input type="text" name="user_job_title" placeholder="職稱">
            <button class="delete">
                <div class="line1"></div>
            </button>
        </div>`)

        $('.delete').on('click', function(){
            $(this).parent().remove()
        })
    })

    // 申請資料使用者在送出的時候就先整理好成dict list
    
})

function sendRequest(){
    //alert($('#appilcationForm').serialize())
    if ($('input[name=is_authenticated]').val() == 'True'){

        let checked = true;

        let users = [];
        $('.apply_peo .item_set1').each(function(){
            if ( // 如果不是全空才加上去
                !((!$(this).children('input[name=user]').val()) & (!$(this).children('input[name=user_affiliation]').val())& (!$(this).children('input[name=user_job_title]').val()))
            ) {
            users.push(
                {
                    'user_name': $(this).children('input[name=user]').val(),
                    'user_affiliation': $(this).children('input[name=user_affiliation]').val(),
                    'user_job_title': $(this).children('input[name=user_job_title]').val(),
                }
            )}
        })

        let cols = ['applicant','phone','address','affiliation','project_name']
        cols.forEach(function(c){
            if (!$(`input[name=${c}]`).val()){
                checked = false;
            }
        })

        if (!$('textarea[name=abstract]').val()){
            checked = false;
        }


        if (checked){
            $.ajax({
                url: "/submit_sensitive_request",
                data: $('#appilcationForm').serialize() + '&users='+ JSON.stringify(users)  + '&csrfmiddlewaretoken=' + $csrf_token +
                '&' + window.location.search.substring(1),
                type: 'POST',
                dataType : 'json',
            })
            .done(function(result) {
                alert('請求已送出，審核完畢後將以email通知')
                window.location.href = '/manager?menu=sensitive'
            })
            .fail(function( xhr, status, errorThrown ) {
                if (xhr.status==504){
                alert('要求連線逾時')
                } else {
                alert('發生未知錯誤！請聯絡管理員')
                }
                console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
            })
        } else {
            alert('請完整填寫表格')
        }
    } else {
    alert('請先登入')
    }
}
