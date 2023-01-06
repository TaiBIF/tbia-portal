// Function to check letters and numbers
function checkPasswordStr(inputText){
    let letterNumber = /^[0-9a-zA-Z]{6,10}$/
    if(inputText.match(letterNumber)){
        return true
    } else {
        return false
    }
    }

function resetPassword(){
    // remove all notice first
    $('#resetForm .noticbox').addClass('d-none')

    let checked = true

    if (!checkPasswordStr($('#resetForm input[name=password]').val())) { // check password
    $('#resetForm input[name=password]').next('.noticbox').removeClass('d-none')
    checked = false
    } 
    
    if ($('#resetForm input[name=password]').val() != $('#resetForm input[name=repassword]').val()) { // check repassword
    $('#resetForm input[name=repassword]').next('.noticbox').removeClass('d-none')
    checked = false
    } 

    if (checked)
    {
        $.ajax({
            url: "/reset_password_submit",
            data: $('#resetForm').serialize() ,
            type: 'POST',
            dataType : 'json',
        })
        .done(function(response) {
        
        if (response.status=='success'){
            alert(response.message)
            location.href="/"
        } else {
            alert(response.message)
        }
            
        })
        .fail(function( xhr, status, errorThrown ) {
        alert('發生未知錯誤！請聯絡管理員')
        console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
        })  
    }
}

$( function() {
    $('.resetPassword').on('click', function(){
        resetPassword()
    })
})