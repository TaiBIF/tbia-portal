var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

$( function() {
    $('.resendEmail').on('click', function(){
        $.ajax({
            url: "/register/resend/verification",
            data: {'email': $('input[name="resend_email"]').val(),csrfmiddlewaretoken: $csrf_token} ,
            type: 'POST',
            dataType : 'json',
        })
        .done(function(response) {
          
          if (response.status=='success'){
            alert('已重新寄送')
          } else {
            alert('發生未知錯誤！請聯絡管理員')
          }
            
        })
        .fail(function( xhr, status, errorThrown ) {
          alert('發生未知錯誤！請聯絡管理員')
          console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
          $('.login_pop').addClass('d-none')
        })      
    })
})
