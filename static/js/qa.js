$( function() {
    $('.qa_list ul li').on('click', function(){
        if ($(this).hasClass('now')){
            $(this).removeClass('now')
        } else {
            $(this).addClass('now')
        }
    })
})