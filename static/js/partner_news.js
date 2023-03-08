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

                if (menu=='list'){
                  n_menu = 'news'
                }
                  
                if (response.page_list.includes(response.current_page-1)){
                  $(`.${n_menu} .item .page_number a.pre`).addClass('changePage');
                  $(`.${n_menu} .item .page_number a.pre`).data('page', response.current_page-1);
                  $(`.${n_menu} .item .page_number a.pre`).data('type', menu);    
                } else {
                    $(`.${n_menu} .item .page_number a.pre`).addClass('pt-none')
                }
    
                let html = ''
                for (let i = 0; i < response.page_list.length; i++) {
                    if (response.page_list[i] == response.current_page){
                        html += ` <a href="javascript:;" class="num now changePage" data-page="${response.page_list[i]}" data-type="${menu}">${response.page_list[i]}</a>  `;
                    } else {
                        html += ` <a href="javascript:;" class="num changePage" data-page="${response.page_list[i]}" data-type="${menu}">${response.page_list[i]}</a>  `
                    }
                }
    
                $(`.${n_menu} .item .page_number a.pre`).after(html)
        
                // 如果有下一頁，改掉next的onclick
                if (response.current_page < response.total_page){
                    $(`.${n_menu} .item .page_number a.next`).addClass('changePage');
                    $(`.${n_menu} .item .page_number a.next`).data('page', response.current_page+1);
                    $(`.${n_menu} .item .page_number a.next`).data('type', menu);
                } else {
                    $(`.${n_menu} .item .page_number a.next`).addClass('pt-none')
                }
    
                $('.changePage').off('click')
                $('.changePage').on('click', function(){
                    changePage($(this).data('page'),$(this).data('type'))
                })        
                
        }
    });

}

(function () {
    Quill.register("modules/imageUploader", ImageUploader);

    var toolbarOptions = [
        [{ 'font': [] }, { 'size': [] }],
        [ 'bold', 'italic', 'underline', 'strike' ],
        [{ 'color': [] }, { 'background': [] }],
        [{ 'list': 'ordered' }, { 'list': 'bullet'}, { 'indent': '-1' }, { 'indent': '+1' }],
        [ 'direction', { 'align': [] }],
        [ 'link', 'image', 'video'],
        [ 'clean' ]
    ]

    var quill = new Quill('#editor', {
        theme: 'snow',   modules: {
            'toolbar': toolbarOptions,
            'imageResize': {
                modules: [ 'Resize', 'DisplaySize', 'Toolbar' ]
            },
            imageUploader: {
                upload: file => {
                  return new Promise((resolve, reject) => {
                    const formData = new FormData();
                    formData.append("image", file);
                    formData.append("csrfmiddlewaretoken", $csrf_token);
  
                    fetch(
                      "/save_news_image",
                      {
                        method: "POST",
                        body: formData
                      }
                    )
                      .then(response => response.json())
                      .then(result => {
                        resolve( '/media/'+ result.data.url);
                      })
                      .catch(error => {
                        reject("Upload failed");
                        console.error("Error:", error);
                      });
                  });
                }
              }
            }
        
      });

      if ($('input[name=news_id]').val()){
        $.ajax({
          url: `/get_news_content?news_id=${$('input[name=news_id]').val()}`,
          type: 'GET',
          success: function(response){
              quill.pasteHTML(response.content);
          }
        });
      }


      
})();


$(document).ready(function () {

    $('.changeMenu').on('click', function(){
        let menu = $(this).data('menu');
      // 如果是edit的話要先把Edit的內容拿掉
      if (menu == 'edit') {
        $('#newsForm input[name=news_id]').val('')
        $('#newsForm input[name=status]').val('pending')
        $('#newsForm input[name=title]').val('')
        $('#newsForm li img.img-style').remove()
        $('#newsForm input[name=image]').val('')

        var element = document.getElementsByClassName("ql-editor");
        element[0].innerHTML = "";
      }

        $('.rightbox_content').addClass('d-none'); 
        $(`.rightbox_content.${menu}`).removeClass('d-none'); 
        changeURL(menu)
    })

    // $('label[for="id_content"]').html('')

    /*
    var $radios = $('#newsForm input:radio[name=type]');
    if (($('input[name=n_type]').val()!='')&&($('input[name=n_type]').val()!='None')){
      $radios.prop('checked', false);

      if($radios.is(':checked') === false) {
          $radios.filter(`[value=${$('input[name=n_type]').val()}]`).prop('checked', true);
      }
    }*/

    $(`a.${ $('input[name=menu]').val() }`).addClass('now')
    $(`a.${ $('input[name=menu]').val() }`).parent(".second_menu").slideToggle();
    $(`.rightbox_content.${ $('input[name=menu]').val() }`).removeClass('d-none')


    $('.submitNews').on('click', function(){
      // remove all notice first
      $('.noticbox').addClass('d-none')
  
      let checked = true;
  
      if (!$('#newsForm input[name=title]').val()){ 
        $('#newsForm input[name=title]').next('.noticbox').removeClass('d-none')
        checked = false
      }  
  
      var regex = /(<([^>]+)>)/ig
      check_body = $('.ql-editor').html()
      //hasText = check_body.replace(regex, "");
    
      if (check_body.replace(regex, "")=='') {
          $('.editor-content').removeClass('d-none')
          checked = false
       }  
  
      if (checked) {
          $('#newsForm').append(`<textarea class="d-none" name="content">${check_body}</textarea>`)
          $('#newsForm').submit()
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
  
})


