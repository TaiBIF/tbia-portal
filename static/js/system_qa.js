
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



  function delete_qa(qa_id){
    $.ajax({
      type: 'POST',
      url: "/delete_qa",
      data: {'qa_id': qa_id},
      headers: {'X-CSRFToken': $csrf_token},
      success: function (response) {
          alert('刪除成功')
          window.location = '/manager/system/qa?menu=list';
      }
    })
  }


$(document).ready(function () {

  $('.changeMenu').on('click', function(){
      let menu = $(this).data('menu');
      $('.rightbox_content').addClass('d-none'); 
      $(`.rightbox_content.${menu}`).removeClass('d-none'); 
      // 如果是edit的話要先把Edit的內容拿掉
      if (menu == 'edit') {
        $('#saveForm textarea[name=answer]').val('')
        $('#saveForm textarea[name=question]').val('')
        $('#saveForm input[name=qa_id]').val('')
        $('#saveForm select[name=qa_type]').val('1')
      }
      changeURL(menu)
  })

  $('.changePage').on('click', function(){
      changePage($(this).data('page'), $(this).data('type'))
  })


  $('.delete_qa').on('click', function(){
    delete_qa($(this).data('qa_id'))
  })


  $('#publish').on('click',function(){
      let checked = true;

      if (!$('#saveForm textarea[name=answer]').val()){ 
          $('#saveForm textarea[name=answer]').next('.noticbox').removeClass('d-none')
          checked = false
      }
        
      if (!$('#saveForm textarea[name=question]').val()){ 
          $('#saveForm textarea[name=question]').next('.noticbox').removeClass('d-none')
          checked = false
      }
      
      if (checked) {
          
          $.ajax({
              type: 'POST',
              url: "/submit_qa",
              data: {'type': $('#saveForm select[name=qa_type]').find(":selected").val(), 
                     'qa_id': $('#saveForm input[name=qa_id]').val(), 
                     'answer': $('#saveForm textarea[name=answer]').val(),
                     'question': $('#saveForm textarea[name=question]').val(),
                     'order': $('#saveForm input[name=order]').val()
                    },
              headers: {'X-CSRFToken': $csrf_token},
              success: function (response) {
                  window.location = '/manager/system/qa?menu=list';
              }
          })

      }
  })

  $(`a.${ $('input[name=menu]').val() }`).addClass('now')
  $(`a.${ $('input[name=menu]').val() }`).parent(".second_menu").slideToggle();
  $(`.rightbox_content.${ $('input[name=menu]').val() }`).removeClass('d-none')

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
          
})



function changePage(page, menu){
$.ajax({
  url: `/change_manager_page?page=${page}&menu=${menu}`,
  type: 'GET',
  success: function(response){
      // 修改表格內容

      $(`.${menu}_table`).html(`
      ${response.header}
      ${response.data}
      `)

      $(`.${menu}_table`).parent().next('.page_number').remove()

      // 修改頁碼
      //if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕
        $(`.${menu}_table`).parent().after(
            `<div class="page_number">
            <a href="javascript:;" class="num changePage" data-page="1" data-type="${menu}">1</a>
            <a href="javascript:;" class="pre"><span></span>上一頁</a>  
            <a href="javascript:;" class="next">下一頁<span></span></a>
            <a href="javascript:;" class="num changePage" data-page="${response.total_page}" data-type="${menu}">${response.total_page}</a>
            </div>`)
    //}		

    let s_menu = ''
    if (menu=='qa') {
      s_menu = 'list'
    }


    let html = ''
    for (let i = 0; i < response.page_list.length; i++) {
        if (response.page_list[i] == response.current_page){
            html += ` <a href="javascript:;" class="num now changePage" data-page="${response.page_list[i]}" data-type="${menu}">${response.page_list[i]}</a>  `;
        } else {
            html += ` <a href="javascript:;" class="num changePage" data-page="${response.page_list[i]}" data-type="${menu}">${response.page_list[i]}</a>  `
        }
    }

    $(`.${s_menu} .item .page_number a.pre`).after(html)

    // 如果有下一頁，改掉next的onclick
    if (response.current_page < response.total_page){
        $(`.${s_menu} .item .page_number a.next`).addClass('changePage');
        $(`.${s_menu} .item .page_number a.next`).data('page', response.current_page+1);
        $(`.${s_menu} .item .page_number a.next`).data('type', menu);
    } else {
        $(`.${s_menu} .item .page_number a.next`).addClass('pt-none')
    }

    // 如果有上一頁，改掉prev的onclick
    if (response.current_page - 1 > 0){
        $(`.${s_menu} .item .page_number a.pre`).addClass('changePage');
        $(`.${s_menu} .item .page_number a.pre`).data('page', response.current_page-1);
        $(`.${s_menu} .item .page_number a.pre`).data('type', menu);    
    } else {
        $(`.${s_menu} .item .page_number a.pre`).addClass('pt-none')
    }

    $('.changePage').off('click')
    $('.changePage').on('click', function(){
        changePage($(this).data('page'),$(this).data('type'))
    })        

    $('.delete_qa').off('click')
    $('.delete_qa').on('click', function(){
      delete_qa($(this).data('qa_id'))
    })
  }
});

}

