var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

function changeURL(menu) {
  history.pushState(null, '', window.location.pathname + '?' + 'menu=' + menu);
}

// 如果按上下一頁
window.onpopstate = function (e) {
  e.preventDefault();

  $('.rightbox_content').addClass('d-none')
  $('.col_menu.second_menu a').removeClass('now')
  $('.col_menu.second_menu').addClass('d-none')

  let queryString = window.location.search;
  let urlParams = new URLSearchParams(queryString);

  let menu = urlParams.get('menu')
  if (menu) {

    $(`a.${menu}`).addClass('now')
    $(`a.${menu}`).parent(".second_menu").slideToggle();

    $(`.rightbox_content.${menu}`).removeClass('d-none')
  }
};



function changePage(page, menu) {
  $.ajax({
    url: `/change_manager_page?page=${page}&menu=${menu}`,
    type: 'GET',
    success: function (response) {

      
      // 保留表格 header 修改表格內容
      $(`.${menu}_table tr:not(.${menu}_table_header)`).remove()
      $(`.${menu}_table`).append(`${response.data}`)

      $(`.${menu}_table`).parent().next('.page_number').remove()


      // 如果有response才顯示?

      if (response.total_page > 0){

        // 修改頁碼
        //if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕
        $(`.${menu}_table`).parent().after(
          `<div class="page_number">
                        <a class="num changePage" data-page="1" data-type="${menu}">1</a>
                        <a class="pre"><span></span>上一頁</a>  
                        <a class="next">下一頁<span></span></a>
                        <a class="num changePage" data-page="${response.total_page}" data-type="${menu}">${response.total_page}</a>
                        </div>`)
        //}		  

        // if (menu == 'list') {
        //   menu = 'news'
        // }

        // let menu = 'news'
        // console.log(menu)
        // let menu = 'list'

        let html = ''
        for (let i = 0; i < response.page_list.length; i++) {
          // console.log(response.page_list[i])
          if (response.page_list[i] == response.current_page) {
            html += ` <a class="num now changePage" data-page="${response.page_list[i]}" data-type="${menu}">${response.page_list[i]}</a>  `;
          } else {
            html += ` <a class="num changePage" data-page="${response.page_list[i]}" data-type="${menu}">${response.page_list[i]}</a>  `
          }
        }

        $(`.${menu} .item .page_number a.pre`).after(html)

        // 如果有下一頁，改掉next的onclick
        if (response.current_page < response.total_page) {
          $(`.${menu} .item .page_number a.next`).addClass('changePage');
          $(`.${menu} .item .page_number a.next`).data('page', response.current_page + 1);
          $(`.${menu} .item .page_number a.next`).data('type', menu);
        } else {
          $(`.${menu} .item .page_number a.next`).addClass('pt-none')
        }

        // 如果有上一頁，改掉prev的onclick
        if (response.current_page - 1 > 0) {
          $(`.${menu} .item .page_number a.pre`).addClass('changePage');
          $(`.${menu} .item .page_number a.pre`).data('page', response.current_page - 1);
          $(`.${menu} .item .page_number a.pre`).data('type', menu);
        } else {
          $(`.${menu} .item .page_number a.pre`).addClass('pt-none')
        }

        $('.changePage').off('click')
        $('.changePage').on('click', function () {
          changePage($(this).data('page'), $(this).data('type'))
        })
      }
    }
  });

}

(function () {
  Quill.register("modules/imageUploader", ImageUploader);

  var toolbarOptions = [
    [{ 'font': [] }, { 'size': [] }],
    ['bold', 'italic', 'underline', 'strike'],
    [{ 'color': [] }, { 'background': [] }],
    [{ 'list': 'ordered' }, { 'list': 'bullet' }, { 'indent': '-1' }, { 'indent': '+1' }],
    ['direction', { 'align': [] }],
    ['link', 'image', 'video'],
    ['clean']
  ]

  var quill = new Quill('#editor', {
    theme: 'snow', modules: {
      'toolbar': toolbarOptions,
      'imageResize': {
        modules: ['Resize', 'DisplaySize', 'Toolbar']
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
                resolve('/media/' + result.data.url);
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

  if ($('input[name=news_id]').val()) {
    $.ajax({
      url: `/get_news_content?news_id=${$('input[name=news_id]').val()}`,
      type: 'GET',
      success: function (response) {
        quill.pasteHTML(response.content);
      }
    });
  }



})();


$(document).ready(function () {

  // 起始頁面
  changePage(1, 'news')

  $('.changeMenu').on('click', function () {
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

    // 類別
    if ($('input[name=n_type]').val() != ''){
      $('select[name=type]').val($('input[name=n_type]').val()); 
      $('select[name=type]').change();
    } 

  $(`a.${$('input[name=menu]').val()}`).addClass('now')
  $(`a.${$('input[name=menu]').val()}`).parent(".second_menu").slideToggle();
  $(`.rightbox_content.${$('input[name=menu]').val()}`).removeClass('d-none')


  $('.submitNews').on('click', function () {
    // remove all notice first
    $('.noticbox').addClass('d-none')

    let checked = true;

    if (!$('#newsForm input[name=title]').val()) {
      $('#newsForm input[name=title]').next('.noticbox').removeClass('d-none')
      checked = false
    }

    var regex = /(<([^>]+)>)/ig
    check_body = $('.ql-editor').html()
    //hasText = check_body.replace(regex, "");

    if (check_body.replace(regex, "") == '') {
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


