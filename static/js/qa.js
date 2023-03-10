$( function() {
    $('.qa_list ul li').on('click', function(){
        if ($(this).hasClass('now')){
            $(this).removeClass('now')
        } else {
            $(this).addClass('now')
        }
    })

    $('.qa_top_item .tabb li').on('click', function(){
        updateQa(1, $(this).data('type'))
    })

    $('.changePage').on('click', function(){
        updateQa($(this).data('page'), $(this).data('type'))
    })

    $('select[name=qa_type]').on('change', function(){
        updateQa(1, $(this).val())
    })

    let selectBox = new vanillaSelectBox("#qa_type",{"placeHolder":"問題類型",search:false, disableSelectAll: true,
    });

    $('.mobile_tab .vsb-main button').css('border','').css('background','')
    $('.mobile_tab span.caret').addClass('d-none')

    $('.mobile_tab .vsb-main button').on('click',function(){
        if ($(this).next('.mobile_tab .vsb-menu').css('visibility')=='visible'){
            $(this).next('.mobile_tab .vsb-menu').addClass('visible')
        } else {
            $(this).next('.mobile_tab .vsb-menu').css('visibility', '')
            $(this).next('.mobile_tab .vsb-menu').removeClass('visible')
        }
    })

    selectBox.setValue('2')
    $('#btn-group-qa_type button span.title').addClass('color-white')

    $('#qa_type').on('change',function(){
          $('#btn-group-qa_type button span.title').addClass('color-white')
    })
})


function updateQa(page, type){


    $('select[name=qa_type]').val(type)

    $('.page_number').html('')
    $('.qa_top_item .tabb li').removeClass('now')
    $(`.qa_top_item .tabb li.qa_${type}`).addClass('now')

    $.ajax({
        url:'/get_qa_list',
        type: 'POST',
        headers:{'X-CSRFToken': $csrf_token},
        data: {'type': type, 'page': page},

        success: function (response, status){ 
          if( response.data.length >0){
            $('.qa_list ul').html('')
            for (let q of response.data) {
                $('.qa_list ul').append(
                    `
                    <li>
                    <div class="questieon">
                      <div class="mark_title">Q</div>
                      <p>${ q.question }</p>
                      <div class="arr"></div>
                    </div>
                    <div class="ans">
                      <div class="mark_title">A</div>
                      <p>${ q.answer }</p>
                    </div>
                    </li>
                `)
            }

            $('.qa_list ul li').off('click')
            $('.qa_list ul li').on('click', function(){
                if ($(this).hasClass('now')){
                    $(this).removeClass('now')
                } else {
                    $(this).addClass('now')
                }
            })        
              
            $('.page_number').remove()
            $('.qa_list').after(`<div class="page_number"></div>`)

              // 修改頁碼
              if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕
                  $(`.page_number`).append(
                    `
                      <a href="javascript:;" class="num changePage" data-page="1" data-type="${type}">1</a>
                      <a href="javascript:;" class="pre">上一頁</a>  
                      <a href="javascript:;" class="next">下一頁</a>
                      <a href="javascript:;" class="num changePage" data-page="${response.total_page}" data-type="${type}">${response.total_page}</a>
                  `)
              }		
                
              if (response.page_list.includes(response.current_page-1)){
                $('.pre').addClass('changePage')
                $('.pre').data('page', response.current_page-1)
                $('.pre').data('type', type)
              } else {
                $('.pre').addClass('pt-none')
              }

              let html = ''
              for (let i = 0; i < response.page_list.length; i++) {
                if (response.page_list[i] == response.current_page){
                  html += ` <a href="javascript:;" class="num now changePage" data-page="${response.page_list[i]}" data-type="${type}">${response.page_list[i]}</a>  `;
                } else {
                  html += ` <a href="javascript:;" class="num changePage" data-page="${response.page_list[i]}" data-type="${type}">${response.page_list[i]}</a>  `
                }
              }

              $('.pre').after(html)
      
              // 如果有下一頁，改掉next的onclick
              if (response.current_page < response.total_page){
                $('.next').addClass('changePage')
                $('.next').data('page', response.current_page+1)
                $('.next').data('type', type)
              } else {
                $('.next').addClass('pt-none')
              }  

              $('.changePage').off('click')
              $('.changePage').on('click', function(){
                updateQa($(this).data('page'), $(this).data('type'))
              })
            } else {
                $('.qa_list ul').html('<li class="no_qa">暫無資料</li>')
            }
            $('.loadingbox').addClass('d-none');
        },
        error: function (xhr, desc, err){
          $('.loadingbox').addClass('d-none');
          alert('未知錯誤，請聯繫管理員');
        }
  });
}
