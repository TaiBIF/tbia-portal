var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

$(function () {
  // 起始頁面
  updateNews('all', 1) 

  // $('.changePage').on('click', function () {
  //   changePage($(this).data('page'), $(this).data('type'))
  // })

  let start_date_picker = new AirDatepicker('#start_date',
    { locale: date_locale });

  let end_date_picker = new AirDatepicker('#end_date',
    { locale: date_locale });

  $('.show_start').on('click', function () {
    if (start_date_picker.visible) {
      start_date_picker.hide();
    } else {
      start_date_picker.show();
    }
  })

  $('.show_end').on('click', function () {
    if (end_date_picker.visible) {
      end_date_picker.hide();
    } else {
      end_date_picker.show();
    }
  })

  $('.updateNews').on('click', function () {
    updateNews($(this).data('type'), 1)
  })

  // 起始類別
  if ($('input[name=news_type]').val() != '') {
    $(`.news_tab_in .li-news-${$('input[name=news_type]').val()}`).addClass('now')
    updateNews($('input[name=news_type]').val(), 1) 

  } else {
    $(`.news_tab_in .li-news-all`).addClass('now')
    updateNews('all', 1) 
  }

  $('.date_select .search_btn').on('click', function () {
    $('.already_selected ul').removeClass('d-none');
    $('.already_selected').data('filter', 'yes');
    $('.already_selected p').html(`${$("#start_date").val()}~${$("#end_date").val()}`);
    $('.news_tab_in li.now').trigger('click')
  })


  $('.already_selected ul li button.xx').on('click', function () {
    $('.already_selected ul').addClass('d-none');
    $('.already_selected').data('filter', 'no');
    //$('.already_selected p').html(`${$( "#start_date" ).val()}~${$( "#end_date" ).val()}`);
    $('.news_tab_in li.now').trigger('click')
  })

});



function changePage(page, type) {
  let current_page = parseInt($('a.num.now').html())
  // 和當前頁碼不同才動作
  if (current_page != page) {
    updateNews(type, page)
  }
}


function updateNews(type, page) {
  $('.news_tab_in li').removeClass('now')
  $(`.li-news-${type}`).addClass('now')

  let query;
  if ($('.already_selected').data('filter') == 'no') {
    query = { 'type': type, 'page': page }
  } else {
    query = {
      'type': type, 'page': page,
      'start_date': $("#start_date").val(),
      'end_date': $("#end_date").val()
    }
  }

  $.ajax({
    url: '/get_news_list',
    type: 'POST',
    headers: { 'X-CSRFToken': $csrf_token },
    data: query,
    success: function (response, status) {
      
      $('.page_number').remove()

      if (response.data.length > 0) {
        $('.news_list').html('')
        for (let d of response.data) {
          $('.news_list').append(
            `<li>
                      <a href="/${$lang}/news/detail/${d.id}" class="imgbox">
                        <img class="img_area" src="${d.image}">
                      </a>
                      <div class="infbox">
                        <div class="center_box">
                          <div class="tag_date">
                            <div class="tag ${d.color}">${gettext(d.type_c)}</div>
                            <p class="date">${d.publish_date}</p>
                          </div>
                          <a href="/${$lang}/news/detail/${d.id}" class="nstitle">
                            ${d.title}
                          </a>
                        </div>
                      </div>
                    </li>`)
        }

        
        $('ul.news_list').after(`<div class="page_number"></div>`)

        // 修改頁碼
        //if (response.page_list.length > 1){  // 判斷是否有下一頁，有才加分頁按鈕
        $(`.page_number`).append(
          `
                      <a class="num changePage" data-page="1" data-type="${type}">1</a>
                      <a class="pre"><span></span>${gettext('上一頁')}</a>  
                      <a class="next">${gettext('下一頁')}<span></span></a>
                      <a class="num changePage" data-page="${response.total_page}" data-type="${type}">${response.total_page}</a>
                  `)
        //}		

        let html = ''
        for (let i = 0; i < response.page_list.length; i++) {
          if (response.page_list[i] == response.current_page) {
            html += ` <a class="num now changePage" data-page="${response.page_list[i]}" data-type="${type}">${response.page_list[i]}</a>  `;
          } else {
            html += ` <a class="num changePage" data-page="${response.page_list[i]}" data-type="${type}">${response.page_list[i]}</a>  `
          }
        }

        $('.pre').after(html)

        // 如果有下一頁，改掉next的onclick
        if (response.current_page < response.total_page) {
          //$('.next').attr('onclick',`changePage(${response.current_page+1}, '${type}')`);
          $('.next').addClass('changePage')
          $('.next').data('page', response.current_page + 1)
          $('.next').data('type', type)
        } else {
          $('.next').addClass('pt-none')
        }


        // 如果有上一頁，改掉prev的onclick  
        if (response.current_page - 1 > 0) {
          $('.pre').addClass('changePage')
          $('.pre').data('page', response.current_page - 1)
          $('.pre').data('type', type)
          //$('.pre').attr('onclick',`changePage(${response.current_page-1}, '${type}')`);
        } else {
          $('.pre').addClass('pt-none')
        }

        $('.changePage').off('click')
        $('.changePage').on('click', function () {
          changePage($(this).data('page'), $(this).data('type'))
        })
      } else {
        $('.news_list').html(`<li>${gettext('無資料')}</li>`)
      }
      $('.loadingbox').addClass('d-none');
    },
    error: function (xhr, desc, err) {
      $('.loadingbox').addClass('d-none');
      alert(gettext('發生未知錯誤！請聯絡管理員'));
    }
  });
}
