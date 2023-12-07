var $csrf_token = $('[name="csrfmiddlewaretoken"]').attr("value");
var $lang = $('[name="lang"]').attr('value');

function toggleSearchBox() {
  if ($(window).width() < 999) {
    $('.top-toggle-btn').off('click');
    $('.top-toggle-btn').on('click', function () {
      $('.searchbox').slideToggle();
    });
  } else {
    $('.top-toggle-btn').off('click');
    $('.top-toggle-btn').on('click', function () {
      $('.searchbox .mb-btn').trigger('click');
    });
  }
}

toggleSearchBox();

$(window).on('resize', function () {
  toggleSearchBox();
});

// function reloadOnWindowResize() {
//   $(window).on('resize', function() {
//     if ($(window).width() < 999) {
//       location.reload(); 
//     }
//   });
// }

// 初始加载时执行一次
// reloadOnWindowResize();



function showLogin() {
  if ($('input[name=is_authenticated]').val() == 'False') {
    $('.login_pop').removeClass('d-none');
    $('.login_pop .loginbox').addClass('d-none');
    $('.login_pop .login_area').removeClass('d-none')
  }
}

// 背景更新通知
function getCurrentNotif() {
  // your function code here
  $.ajax({
    url: "/get_current_notif?lang=" + $lang,
    type: 'GET',
    success: function (response) {
      if (response.count > 0) {
        $('.num_message').html(response.count)
        $('.num_message').removeClass('d-none')
      } else {
        $('.num_message').addClass('d-none')
      }
      $('.message_list').html(response.notif)

      $('.redirectToAdmin').off('click')
      $('.redirectToAdmin').on('click', function () {

        let n_id = $(this).data('nid')
        $.ajax({
          url: `/update_this_read?n_id=${n_id}`,
          type: 'GET',
          success: function () { }
        })
        window.location = $(this).data('href')
      })
    }
  });
  if ($('input[name=is_authenticated]').val() == 'True') {
    setTimeout(getCurrentNotif, 5000);
  }
}

if ($('input[name=is_authenticated]').val() == 'True') {
  getCurrentNotif();
}



function isOverflown(element) {
  return element.scrollHeight > element.clientHeight || element.scrollWidth > element.clientWidth;
}




var CaptchaCallback = function () {
  jQuery('.g-recaptcha').each(function (index, el) {
    grecaptcha.render(el, {
      'sitekey': jQuery(el).attr('data-sitekey'),
      'theme': jQuery(el).attr('data-theme'),
      'size': jQuery(el).attr('data-size'),
      //'tabindex' : jQuery(el).attr('data-tabindex'),
    });
  });
};

$(function () {

  $('#search_full_form_top').on('submit', function(event){
    event.preventDefault()

    if ($('.top_search_full_keyword').val().length > 2000) {
      alert(gettext('您查詢的條件網址超過 2000 個字元，可能無法在所有瀏覽器中正常運作。'))
    } else {
      window.location = `/${$lang}/search/full?keyword=${$('.top_search_full_keyword').val()}`
    }

  })


  $('.language-item').on('click', function (event) {
    $('input[name=language]').val($(this).data('value'))
    console.log( $('input[name=language]').val())
    $('#language-selected').submit()
  });


  if (!isOverflown($('.message_list')[0])) {
    $('.message_list li:last-child').addClass('box-radius-10px')
  }


  let selectBoxFP = new vanillaSelectBox("#feedback_partner", {
    "placeHolder": $('#feedback_partner').attr('placeholder'), search: false, disableSelectAll: true,
  });

  let selectBoxFT = new vanillaSelectBox("#feedback_type", {
    "placeHolder": $('#feedback_type').attr('placeholder'), search: false, disableSelectAll: true,
  });


  // $('span.caret').addClass('d-none')

  /*
  $('.vsb-main button').on('click',function(){
      if ($(this).next('.vsb-menu').css('visibility')=='visible'){
          $(this).next('.vsb-menu').addClass('visible')
      } else {
          $(this).next('.vsb-menu').css('visibility', '')
          $(this).next('.vsb-menu').removeClass('visible')
      }
  })*/

  $('#feedback_partner').on('change', function () {
    if ($('#btn-group-feedback_partner .vsb-menu ul li.active').length > 0) {
      $('#btn-group-feedback_partner button span.title').addClass('black').removeClass('color-707070')
    } else {
      $('#btn-group-feedback_partner button span.title').addClass('color-707070').removeClass('black')
    }
  })

  $('#feedback_type').on('change', function () {
    if ($('#btn-group-feedback_type .vsb-menu ul li.active').length > 0) {
      $('#btn-group-feedback_type button span.title').addClass('black').removeClass('color-707070')
    } else {
      $('#btn-group-feedback_type button span.title').addClass('color-707070').removeClass('black')
    }
  })


  $('.back-to-index').on('click', function () {
    window.location.href = '/'
  })

  $('.forget-psw').on('click', function () {
    $('.login_pop .loginbox').addClass('d-none')
    $('.login_pop .password_area').removeClass('d-none')
  })

  $('.i-register').on('click', function () {
    // 移除原本的錯誤tag
    $('#registerForm .noticbox').addClass('d-none')

    $('.login_pop .loginbox').addClass('d-none')
    $('.login_pop .register_area').removeClass('d-none')
  })

  $('.back-login').on('click', function () {
    $('.login_pop .loginbox').addClass('d-none')
    $('.login_pop .login_area').removeClass('d-none')
  })

  $('.member_slimenu ul li').on('click', function () {
    window.location = $(this).data('href')
  })


  $('.redirectToAdmin').on('click', function () {

    let n_id = $(this).data('nid')
    $.ajax({
      url: `/update_this_read?n_id=${n_id}`,
      type: 'GET',
      success: function () { }
    })
    window.location = $(this).data('href')
  })

  /*
  $('.updateThisRead').on('click', function(){
      let n_id = $(this).data('nid')
      $.ajax({
      url: `/update_this_read?n_id=${n_id}`,
      type: 'GET',
      success: function(response){
          $(`.message_list li[data-nid=${n_id}] .dottt`).addClass('d-none')
          if (response.count > 0){
              $('.num_message').html(response.count)
          } else {
              $('.num_message').addClass('d-none')
          }
      }
      });
  })*/

  $('.updateIsRead').on('click', function () {
    $.ajax({
      url: "/update_is_read",
      type: 'GET',
      success: function () {
        $('.message_list li .dottt, .num_message, .noti-dottt').addClass('d-none')
      }
    });
  })



  $('.showFeedback').on('click', function () {
    $('.feedback-pop').removeClass('d-none')
  })

  $('.showLogin').on('click', function () {
    showLogin()
  })

  $('.login-onclick').on('click', function () {
    login()
  })

  $('.register-onclick').on('click', function () {
    register()
  })

  $('.feedback-pop .send').on('click', function () {


    if ((!$('#feedback_form #g-recaptcha-response').val()) | (!$('#feedback_form select[name=partner_id]').val()) |
      (!$('#feedback_form select[name=type]').val()) | (!validateEmail($('#feedback_form input[name=email]').val())) |
      (!$('#feedback_form textarea[name=content]').val())) {
      alert(gettext('請完整填寫表格並檢查Email格式是否正確'))
    } else {

      $.ajax({
        url: "/send_feedback",
        data: $('#feedback_form').serialize() + '&csrfmiddlewaretoken=' + $csrf_token,
        type: 'POST',
      })
        .done(function (response) {
          alert(gettext('謝謝您的回饋，我們將會儘速回覆'))

          $('.feedback-pop').addClass('d-none')
        })
        .fail(function (xhr, status, errorThrown) {
          alert(gettext('發生未知錯誤！請聯絡管理員'))
          console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
          $('.login_pop').addClass('d-none')

        })
    }

  })

  $('.google_login').on('click', function () {

    let next_url = window.location.pathname;

    if ('URLSearchParams' in window) {
      var searchParams = new URLSearchParams(window.location.search)
      next_url = window.location.pathname + '?' + searchParams.toString();
    }


    $('#googleForm').attr('action', "/accounts/google/login/?next="+ "/login/google/callback?next2=" + encodeURIComponent(next_url))
    $('#googleForm').submit()

  })



  $('.resetbtn').on('click', function () {
    $.ajax({
      url: "/send_reset_password",
      data: { 'email': $('input[name=reset_email]').val(), csrfmiddlewaretoken: $csrf_token },
      type: 'POST',
      dataType: 'json',
    })
      .done(function (response) {
        alert(gettext(response.message))
      })
      .fail(function (xhr, status, errorThrown) {
        alert(gettext('發生未知錯誤！請聯絡管理員'))
        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        $('.login_pop').addClass('d-none')

      })
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
});

/*
// detect event on show / hide
(function ($) {
  $.each(['show', 'hide'], function (i, ev) {
    var el = $.fn[ev];
    $.fn[ev] = function () {
      this.trigger(ev);
      return el.apply(this, arguments);
    };
  });
})(jQuery);
// loader
var ajaxLoadTimeout;
$(document).ajaxStart(function() {
    ajaxLoadTimeout = setTimeout(function() { 
        $(".loading_area").removeClass('d-none');
    }, 1000);

}).ajaxComplete(function() {
    clearTimeout(ajaxLoadTimeout);
    $(".loading_area").addClass('d-none');
});
*/


window.addEventListener('error', function (event) {
  $(".loading_area").addClass('d-none');
  // clearTimeout(ajaxLoadTimeout);
  // alert('發生未知錯誤！請通知管理員')
})

$(function () {
  $(window).resize(function () {
    if ($(window).width() > 768) {
      $('.mb_bmenu').hide()
      $('.hmenu').removeClass('active')
    }
  })

  $(".hmenu").on("click", function () {
    $(".hmenu").toggleClass("active");
    $(".mb_bmenu").slideToggle();
  });
});


$('.ringbox').on('click', function () {
  if ($(this).hasClass('mb_open')) {
    $(this).removeClass('mb_open');
  } else {
    $(this).addClass('mb_open');
  }
}).children('.messagebox .message_list').click(function () {
  return false;
});


$('.rd_mb_two_menu_li').on('click', function (event) {
  event.preventDefault();
  if ($(this).closest('li').hasClass('now')) {
    $(this).removeClass('now');
    $(this).find('.mbmu2').slideUp();
  } else {
    $(this).addClass('now');
    $(this).find('.mbmu2').slideDown();
  }
});

$(".mbmu2 a").on('click', function () {
  window.location = this.href;
})

$(".popbg .xx").click(function (e) {
  if ($(e.target).hasClass("xx")) $(".popbg").addClass('d-none');
});

// LOGIN 
//https://emailregex.com
function validateEmail(inputText) {
  let mailformat = /(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])/
  if (inputText.match(mailformat)) {
    return true
  } else {
    return false
  }
}

// Function to check letters and numbers
function checkPasswordStr(inputText) {
  let letterNumber = /^[0-9a-zA-Z]{6,10}$/
  if (inputText.match(letterNumber)) {
    return true
  } else {
    return false
  }
}


function login() {

  // remove all notice first
  $('#loginForm .noticbox').addClass('d-none')

  let checked = true

  if (!validateEmail($('#loginForm input[name=email]').val())) { // check email
    $('#loginForm input[name=email]').next('.noticbox').removeClass('d-none')
    checked = false
  }


  if ($('#loginForm #g-recaptcha-response').val() == '') { // check email
    $('#loginForm .g-recaptcha').next('.noticbox').removeClass('d-none')
    checked = false
  }

  if (!checkPasswordStr($('#loginForm input[name=password]').val())) { // check password
    $('#loginForm input[name=password]').next('.noticbox').removeClass('d-none')
    checked = false
  }

  if (checked) {
    $.ajax({
      url: "/login",
      data: $('#loginForm').serialize(),
      type: 'POST',
      dataType: 'json',
    })
      .done(function (response) {

        if (response.status == 'success') {
          location.reload()
        } else {
          alert(gettext(response.message))
        }
      })
      .fail(function (xhr, status, errorThrown) {
        alert(gettext('發生未知錯誤！請聯絡管理員'))
        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        $('.login_pop').addClass('d-none')
      })
  }
}

function register() {
  // remove all notice first
  $('#registerForm .noticbox').addClass('d-none')

  let checked = true

  if (!$('#registerForm input[name=name]').val()) { // check name
    $('#registerForm input[name=name]').next('.noticbox').removeClass('d-none')
    checked = false
  }

  if (!validateEmail($('#registerForm input[name=email]').val())) { // check email
    $('#registerForm input[name=email]').next('.noticbox').removeClass('d-none')
    checked = false
  }

  if (!checkPasswordStr($('#registerForm input[name=password]').val())) { // check password
    $('#registerForm input[name=password]').next('.noticbox').removeClass('d-none')
    checked = false
  }

  if ($('#registerForm input[name=password]').val() != $('#registerForm input[name=repassword]').val()) { // check repassword
    $('#registerForm input[name=repassword]').next('.noticbox').removeClass('d-none')
    checked = false
  }

  if (checked) {
    $.ajax({
      url: "/register",
      data: $('#registerForm').serialize(),
      type: 'POST',
      dataType: 'json',
    })
      .done(function (response) {

        if (response.status == 'success') {
          window.location.href = `/${$lang}/register/verification`;

        } else {
          alert(gettext(response.message))
          $('.login_pop').addClass('d-none')
        }

      })
      .fail(function (xhr, status, errorThrown) {
        alert(gettext('發生未知錯誤！請聯絡管理員'))
        console.log('Error: ' + errorThrown + 'Status: ' + xhr.status)
        $('.login_pop').addClass('d-none')
      })
  }
}

$('.login_pop').on('show', function () {
  $('.login_pop input').not('input[type="hidden"]').val('');
  $('.login_pop .noticbox').addClass('d-none')
})


