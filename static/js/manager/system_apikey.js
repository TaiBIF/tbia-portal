var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");

function apikeyPost(url, data) {
  return $.ajax({
    url: url,
    type: 'POST',
    dataType: 'json',
    data: Object.assign({ csrfmiddlewaretoken: $csrf_token }, data),
  }).fail(function (xhr, status, errorThrown) {
    alert(gettext('發生未知錯誤！請聯絡管理員'))
    console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
  })
}

function copyText(text) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(function () { alert('已複製') })
  } else {
    prompt('請手動複製', text)
  }
}

function renderPageNumber(response) {
  $('.apikey_table').parent().next('.page_number').remove()
  if (!(response.total_page > 0)) return

  let $p = $('<div class="page_number"></div>')
  let $pre = $('<a class="pre"><span></span>上一頁</a>')
  let $next = $('<a class="next">下一頁<span></span></a>')

  $p.append(`<a class="num" data-page="1">1</a>`).append($pre)
  response.page_list.forEach(function (n) {
    $p.append(` <a class="num${n == response.current_page ? ' now' : ''}" data-page="${n}">${n}</a> `)
  })
  $p.append($next).append(`<a class="num" data-page="${response.total_page}">${response.total_page}</a>`)

  if (response.current_page > 1) { $pre.attr('data-page', response.current_page - 1) } else { $pre.addClass('pt-none') }
  if (response.current_page < response.total_page) { $next.attr('data-page', response.current_page + 1) } else { $next.addClass('pt-none') }

  $p.find('a[data-page]').on('click', function () { getApikeyList($(this).attr('data-page')) })
  $('.apikey_table').parent().after($p)
}

function getApikeyList(page) {
  apikeyPost('/get_apikey_list', { page: page }).done(function (response) {
    $('.apikey_table tr:not(.apikey_table_header)').remove()

    response.data.forEach(function (r) {
      let $tr = $('<tr></tr>')
      $tr.append($('<td></td>').text('#' + r.id))
      $tr.append($('<td></td>').append(
        $('<span class="apikey-mask"></span>').text(r.key),
        $('<button type="button" class="btn-style1 revealApikey">顯示</button>').attr('data-id', r.id)
      ))
      $tr.append($('<td></td>').text(r.applicant))
      $tr.append($('<td></td>').text(r.user))
      $tr.append($('<td></td>').text(r.partner))
      $tr.append($('<td></td>').text(r.created))
      $tr.append($('<td></td>').text(r.expired))
      $tr.append($('<td></td>').text(r.status_display))
      let $action = $('<td></td>')
      if (r.status == 'pass') {
        $action.append($('<button type="button" class="btn-style1 disableApikey">停用</button>').attr('data-id', r.id))
      } else if (r.can_renew) {
        $action.append($('<button type="button" class="btn-style1 renewApikey">更新key</button>').attr('data-id', r.id))
      }
      $tr.append($action)
      $('.apikey_table').append($tr)
    })

    renderPageNumber(response)
    $('.apikey_table').data('page', response.current_page)
  })
}

function resetForm() {
  $('#apikeyForm input[name=user_id]').val('')
  $('#apikeyForm input[name=applicant]').val('')
  $('#apikeyForm select[name=partner_id]').val('')
  $('.apikey-user-result').addClass('d-none').text('')
  $('.createApikey').prop('disabled', true)
}

$(document).ready(function () {

  $(".mb_fixed_btn").on("click", function () {
    $(".mbmove").toggleClass("open");
    $(this).toggleClass("now");
  });

  getApikeyList(1)

  // 查詢使用者
  $('.searchApikeyUser').on('click', function () {
    resetForm()
    $('.apikey-new').addClass('d-none')
    let email = $.trim($('#apikeyForm input[name=email]').val())
    if (!email) return

    apikeyPost('/get_apikey_user', { email: email }).done(function (response) {
      if (response.status != 'success') {
        $('.apikey-user-result').removeClass('d-none').text(response.message)
        return
      }
      let u = response.user
      $('#apikeyForm input[name=user_id]').val(u.id)
      $('#apikeyForm input[name=applicant]').val(u.name)
      $('#apikeyForm select[name=partner_id]').val(u.partner_id || '')
      $('.apikey-user-result').removeClass('d-none')
        .text(`使用者：${u.name} (${u.email})　註冊方式：${u.register_method || '-'}`)
      $('.createApikey').prop('disabled', false)
    })
  })

  // email 修改後須重新查詢
  $('#apikeyForm input[name=email]').on('input', resetForm)
    .on('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); $('.searchApikeyUser').trigger('click') }
    })

  // 新增
  $('.createApikey').on('click', function () {
    $('.noticbox').addClass('d-none')
    if (!$.trim($('#apikeyForm input[name=applicant]').val())) {
      $('#apikeyForm input[name=applicant]').next('.noticbox').removeClass('d-none')
      return
    }
    if (!confirm('確定要新增API key？')) return

    let $btn = $(this).prop('disabled', true)
    apikeyPost('/create_apikey', {
      user_id: $('#apikeyForm input[name=user_id]').val(),
      applicant: $('#apikeyForm input[name=applicant]').val(),
      partner_id: $('#apikeyForm select[name=partner_id]').val(),
    }).done(function (response) {
      if (response.status != 'success') {
        alert(response.message)
        $btn.prop('disabled', false)
        return
      }
      $('.apikey-new-key').text(response.key)
      $('.apikey-new').removeClass('d-none')
      $('#apikeyForm input[name=email]').val('')
      resetForm()
      getApikeyList(1)
    }).fail(function () { $btn.prop('disabled', false) })
  })

  $('.copyNewKey').on('click', function () {
    copyText($('.apikey-new-key').text())
  })

  // 顯示完整 key
  $('.apikey_table').on('click', '.revealApikey', function () {
    let $btn = $(this)
    apikeyPost('/reveal_apikey', { id: $btn.attr('data-id') }).done(function (response) {
      if (response.status != 'success') { alert(response.message); return }
      $btn.siblings('.apikey-mask').text(response.key)
      $btn.removeClass('revealApikey').addClass('copyApikey').text('複製')
    })
  })

  $('.apikey_table').on('click', '.copyApikey', function () {
    copyText($(this).siblings('.apikey-mask').text())
  })

  // 停用
  $('.apikey_table').on('click', '.disableApikey', function () {
    if (!confirm('停用後無法復原，確定要停用此API key？')) return
    apikeyPost('/disable_apikey', { id: $(this).attr('data-id') }).done(function (response) {
      if (response.status != 'success') { alert(response.message); return }
      getApikeyList($('.apikey_table').data('page') || 1)
    })
  })

  // 更新 key（過期 / 停用 → 產生新 key）
  $('.apikey_table').on('click', '.renewApikey', function () {
    if (!confirm('將為此申請者產生新的API key，確定要更新？')) return
    apikeyPost('/renew_apikey', { id: $(this).attr('data-id') }).done(function (response) {
      if (response.status != 'success') { alert(response.message); return }
      $('.apikey-new-key').text(response.key)
      $('.apikey-new').removeClass('d-none')
      $('html, body').animate({ scrollTop: $('.apikey-new').offset().top - 100 }, 300)
      getApikeyList(1)
    })
  })

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
