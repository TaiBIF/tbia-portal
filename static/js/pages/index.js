var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");


$(document).ready(function () {

  $('.index-search-box').on('click', function(){
    window.location = $(this).data('href')
  })

  $('.search_full_button').on('click', function(){
    $('#search_full_form').submit()
  })

  $('#search_full_form').on('submit', function(event){
    event.preventDefault()

    if ($('.search_full_keyword').val().length > 2000) {
      alert(gettext('您查詢的條件網址超過 2000 個字元，可能無法在所有瀏覽器中正常運作。'))
    } else {
      window.location = `/${$lang}/search/full?keyword=${$('.search_full_keyword').val().replace(/&/g, "%26")}`
    }

  })

  $('.updateNews').on('click', function () {
    updateNews($(this).data('type'), 1)
  })

  gsap.registerPlugin(ScrollTrigger);

  ScrollTrigger.create({
    trigger: ".section_2",
    start: "top-=45% top",
    // markers: true,
    onEnter: function () {
      $(".section_2").addClass("vivi");
    },
  });
  ScrollTrigger.create({
    trigger: ".section_3",
    start: "top-=80% top",
    // markers: true,
    onEnter: function () {
      $(".section_3").addClass("vivi");
    },
  });
  ScrollTrigger.create({
    trigger: ".section_4",
    start: "top-=80% top",
    // markers: true,
    onEnter: function () {
      $(".section_4").addClass("vivi");
    },
  });


  $('.edu_tag li').click(function () {
    let li_element = $(this)
    let type = this.id
    $.ajax({
      url: "/get_resource_list",
      data: {
        type: type,
        lang: $lang,
        csrfmiddlewaretoken: $csrf_token,
      },
      type: 'POST',
      dataType: 'json',
    })
      .done(function (response) {
        // change active tab
        $('.edu_tag li').removeClass('now');
        li_element.addClass('now');
        // remove all resources first
        $('.edu_list li').remove()
        // append rows
        if (type == 'all') {
          $('.edu_list').append(`
            <li>
            <div class="item">
              <div class="cate_dbox">
                <div class="catepin"><i class="fa-solid fa-thumbtack transform315"></i></div>
              </div>
              <a href="/${$lang}/resources/link" class="title" target="_blank">${gettext("國內外各大資料庫及推薦網站連結")}</a>
            </div>
            </li> 
            <li>
            <div class="item">
              <div class="cate_dbox">
                <div class="catepin"><i class="fa-solid fa-thumbtack transform315"></i></div>
              </div>
              <a href="https://tbia.github.io/docs/" class="title" target="_blank">${gettext("TBIA文件網站")}</a>
            </div>
            </li>
            <li class="show_tech">
            <div class="item">
              <div class="cate_dbox">
              <div class="catepin"><i class="fa-solid fa-thumbtack transform315"></i></div>
              </div>
              <a class="title ">${gettext("生物多樣性資料庫共通查詢系統教學說明")}</a>
            </div>
          </li>
  
            `)
        }

        if (response.rows.length > 0) {
          for (let i = 0; i < response.rows.length; i++) {

           if (response.rows[i].cate == 'link'){
              $('.edu_list').append(`
              <li>
                <div class="item">
                <div class="cate_dbox">
                  <div class="cate ${response.rows[i].cate}">${response.rows[i].extension}</div>
      
                  <div class="date">${response.rows[i].date}</div>
                </div>
                <a href="${response.rows[i].url}" class="title" target="_blank">${gettext(response.rows[i].title)}</a>
                </div>
              </li>`)
            } else {
              $('.edu_list').append(`
              <li>
                <div class="item">
                  <div class="cate_dbox">
                    <div class="cate ${response.rows[i].cate}">${response.rows[i].extension}</div>
                    ${ response.rows[i].doc_url ? `<div class="cate web"><a href="${response.rows[i].doc_url}" target="_blank" >WEB <i class="fa-solid fa-link"></i></a></div>` : '' }      
                    <div class="date">${response.rows[i].date}</div>
                  </div>
                  <a href="/media/${response.rows[i].url}" class="title" target="_blank">${gettext(response.rows[i].title)}</a>
                  <a href="/media/${response.rows[i].url}" download class="dow_btn"> </a>
                </div>
              </li>`)
            }
          }
        } else {
          // if no row, show '無資料'
          $('.edu_list').append(`<li>
            <div class="item">
              <div class="cate_dbox">
              </div>
              <a class="title">${gettext('無資料')}</a>
            </div>
          </li>`)
        }
      })
      .fail(function (xhr, status, errorThrown) {
        alert(gettext('發生未知錯誤！請聯絡管理員'))
        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
      })
  })


});



function updateNews(type, page) {
  $('.news_tab li').removeClass('now')
  $(`.li-news-${type}`).addClass('now')
  $.ajax({
    url: '/get_news_list',
    type: 'POST',
    headers: { 'X-CSRFToken': $csrf_token },
    data: { 'type': type, 'page': page, 'from_index': 'yes' },
    success: function (response, status) {
      if (response.data.length > 0) {
        $('.news_list').html('')
        for (let d of response.data) {
          $('.news_list').append(
            `
                    <li>
                      <a href="/${$lang}/news/detail/${d.id}" target="_blank" class="imgbox">
                        <img class="img_area" src="${d.image}">
                      </a>
                      <div class="infbox">
                        <div class="center_box">
                          <div class="tag_date">
                            <div class="tag ${d.color}">${gettext(d.type_c)}</div>
                            <p class="date">${d.publish_date}</p>
                          </div>
                          <a href="/${$lang}/news/detail/${d.id}" target="_blank" class="nstitle">
                            ${d.title}
                          </a>
                        </div>
                      </div>
                    </li>
                    `
          )
        }
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