
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


      (function () {
      //  Quill.register("modules/imageUploader", ImageUploader);
    
        var toolbarOptions = [
            [{ 'font': [] }, { 'size': [] }],
            [ 'bold', 'italic', 'underline', 'strike' ],
            [{ 'color': [] }, { 'background': [] }],
            // [{ 'script': 'super' }, { 'script': 'sub' }],
            // [{ 'header': '1' }, { 'header': '2' }, 'blockquote', 'code-block' ],
            [{ 'list': 'ordered' }, { 'list': 'bullet'}, { 'indent': '-1' }, { 'indent': '+1' }],
            [ 'direction', { 'align': [] }],
            [ 'link'],
            // , 'formula' ],
            [ 'clean' ]
      ]
    
        var quill = new Quill('#editor', {
            theme: 'snow',   modules: {
                'toolbar': toolbarOptions,
                }
            
          });
    
          $.ajax({
            url: `/get_link_content`,
            type: 'GET',
            success: function(response){
                console.log(response)
                quill.pasteHTML(response.content);
            }
        });
    
    
          
    })();
    

    function deleteResource(resource_id){
        $.ajax({
            type: 'POST',
            url: "/delete_resource",
            data: {'resource_id': resource_id},
            headers: {'X-CSRFToken': $csrf_token},
            success: function (response) {
                alert('刪除成功')
                window.location = '/manager/system/resource?menu=list';
            }
        })
    }
    
  $(document).ready(function () {


    $('.submitLink').on('click', function(){    
        $('#linkForm').append(`<textarea class="d-none" name="content">${$('.ql-editor').html()}</textarea>`)
        $('#linkForm').submit()
    })
    

      $('.changeMenu').on('click', function(){
          let menu = $(this).data('menu');
          if (menu == 'edit') {
            $('#saveForm input[name=resource_id]').val('')
            $('#saveForm select[name=resource_type]').val('')
            $('#saveForm input[name=file]').val('')
            $('#saveForm input[name=url]').val('')
            $('#preview').parent('li').html(`<span id="preview" class="d-none"></span>`)
          }
  
          $('.rightbox_content').addClass('d-none'); 
          $(`.rightbox_content.${menu}`).removeClass('d-none'); 
          changeURL(menu)
      })

      $('.changePage').on('click', function(){
          changePage($(this).data('page'), $(this).data('type'))
      })

      $('label[for="id_content"]').html('')

      $('#link_button').on('click',function(){
          $('.rightbox_content').addClass('d-none')
          $('.rightbox_content.edit-link').removeClass('d-none')
      })

      $('.delete_resource').on('click', function(){
        deleteResource($(this).data('resource_id'))
      })

      $('#save_resource_file').on('click',function(){
          $('.noticbox').addClass('d-none')
          var form = new FormData()
          form.append('file', $('#file')[0].files[0])
  
          $.ajax({
              type: 'POST',
              url: "/save_resource_file",
              data: form,
              processData: false,
              contentType: false,
              headers: {'X-CSRFToken': $csrf_token},
              success: function (response) {
                  if (response.url != null){
                      $('#preview').html(`目前檔案：${response['filename']} <a target="_blank" href="/media/${response['url']}">(預覽)</a>`)
                      $('#preview').removeClass('d-none')
                      $('#saveForm input[name=url]').val(response['url'])
                  } else {
                      $('#preview').addClass('d-none')
                      $('#saveForm input[name=url]').val('')
                  }
              }
              .fail(function( xhr, status, errorThrown ) {
                alert('發生未知錯誤！請聯絡管理員')
                console.log( 'Error: ' + errorThrown + 'Status: ' + xhr.status)
                })
            })
        })

      // TODO 還要確認有沒有上傳檔案 filename統一改成帶有resources/的檔名
      $('#publish').on('click',function(){
          let checked = true;

          if ($('#saveForm input[name=title]').val()== ''){
              $('#saveForm input[name=title]').next('.noticbox').removeClass('d-none')
              checked = false
          } 
          
          if ($('#saveForm input[name=url]').val()=='') {
              $('#file_error').removeClass('d-none')
              checked = false
          } 
          
          if (checked) {
              
              $.ajax({
                  type: 'POST',
                  url: "/submit_resource",
                  data: {'url':$('#saveForm input[name=url]').val() , 'type': $('#saveForm select[name=resource_type]').find(":selected").val(), 'resource_id': $('#saveForm input[name=resource_id]').val(), 'title': $('#saveForm input[name=title]').val()},
                  headers: {'X-CSRFToken': $csrf_token},
                  success: function (response) {
                      window.location = '/manager/system/resource?menu=list';
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
          if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕
            $(`.${menu}_table`).parent().after(
                `<div class="page_number">
                <a href="javascript:;" class="num changePage" data-page="1" data-type="${menu}">1</a>
                <a href="javascript:;" class="pre">上一頁</a>  
                <a href="javascript:;" class="next">下一頁</a>
                <a href="javascript:;" class="num changePage" data-page="${response.total_page}" data-type="${menu}">${response.total_page}</a>
                </div>`)
        }		
    
        let s_menu = ''
        if (menu=='resource') {
          s_menu = 'list'
        }

        if (response.page_list.includes(response.current_page-1)){
            $(`.${s_menu} .item .page_number a.pre`).addClass('changePage');
            $(`.${s_menu} .item .page_number a.pre`).data('page', response.current_page-1);
            $(`.${s_menu} .item .page_number a.pre`).data('type', menu);    
        } else {
            $(`.${s_menu} .item .page_number a.pre`).addClass('pt-none')
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

        $('.changePage').off('click')
        $('.changePage').on('click', function(){
            changePage($(this).data('page'),$(this).data('type'))
        })        
            
        $('.delete_resource').off('click')
        $('.delete_resource').on('click', function(){
            deleteResource($(this).data('resource_id'))
          })            
  }
  });

}

