$(document).ready(function () {

  $(".mb_fixed_btn").on("click", function () {
    $(".mbmove").toggleClass("open");
    $(this).toggleClass("now");
  });

  $('.updateIndexEvent').on('click', function () {
    $('.noticbox').addClass('d-none')
    let checked = true;

    if (!$('input[name=text_zh]').val()) {
      $('input[name=text_zh]').next('.noticbox').removeClass('d-none'); checked = false
    }
    if (!$('input[name=url_zh]').val()) {
      $('input[name=url_zh]').next('.noticbox').removeClass('d-none'); checked = false
    }

    if (checked) {
      $.ajax({
        url: "/update_index_event",
        data: $('#indexEventForm').serialize(),
        type: 'POST',
        dataType: 'json',
      })
        .done(function (response) {
          if (response.status == 'success') { alert('修改成功') }
        })
        .fail(function (xhr, status, errorThrown) {
          alert(gettext('發生未知錯誤！請聯絡管理員'))
          console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        })
    }
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