var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");
var $lang = $('[name="lang"]').attr('value');

$(function () {

  // default active page
  if (($('input[name=ark_type]').val() != 'all') & ($('input[name=ark_type]').val() != '')) {
    $('.news_tab_in li').removeClass('now');
    $(`.li-resource-${$('input[name=ark_type]').val()}`).addClass('now');
    updateArk($('input[name=ark_type]').val(), 1)
  }


  // 起始類型
  if ($('input[name=ark_type]').val() != '') {
    $(`.news_tab_in .li-resource-${$('input[name=ark_type]').val()}`).addClass('now')
    updateArk($('input[name=ark_type]').val(), 1)

  }

  $('.updateArk').on('click', function () {
    updateArk($(this).data('type'), 1)
  })

});


function updateArk(type, page) {


  $('.news_tab_in li').removeClass('now')
  $(`.li-resource-${type}`).addClass('now')


  let query;
  if ($('.already_selected').data('filter') == 'no') {
    query = {
      'type': type,
      'from': 'resource',
      'get_page': page,
      'lang': $lang,
    }
  } else {
    query = {
      'type': type,
      'get_page': page,
      'lang': $lang,
    }
  }

  $.ajax({
    url: "/get_ark_list",
    data: query,
    headers: { 'X-CSRFToken': $csrf_token },
    type: 'POST',
    dataType: 'json',
  })
    .done(function (response) {

      // remove all resources first
      $('.ark_table tr:not(.first-row)').remove()
      $('.page_number').remove()

      // append rows
      if (response.rows.length > 0) {
        for (let i = 0; i < response.rows.length; i++) {

          $('.ark_table').append(
            `<tr>
                <td><a href="${response.rows[i].ark_href}" target="_blank">${response.rows[i].ark}</a></td>
                <td><a href="${response.rows[i].url}" target="_blank">${response.rows[i].url}</a></td>
                <td>${response.rows[i].created}</td>
              </tr>`
          )
        }

        // 修改頁碼
        $('.result_table').after(`<div class="page_number"></div>`)

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
          $('.next').addClass('changePage')
          $('.next').data('page', response.current_page + 1)
          $('.next').data('type', type)
        } else {
          $('.next').addClass('pt-none')
        }

        if (response.current_page - 1 > 0) {
          $('.pre').addClass('changePage')
          $('.pre').data('page', response.current_page - 1)
          $('.pre').data('type', type)
        } else {
          $('.pre').addClass('pt-none')
        }

        $('.changePage').off('click')
        $('.changePage').on('click', function () {
          updateArk($(this).data('type'), $(this).data('page'))
        })


      }

    })
    .fail(function (xhr, status, errorThrown) {
      alert(gettext('發生未知錯誤！請聯絡管理員'))

      console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
    })
}