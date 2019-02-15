
// Image preview code below borrowed from https://codepen.io/gab5a430/pen/jPNXeX
function readURL(input) {

    if (input.files && input.files[0]) {
        var reader = new FileReader();
        var filename = $("#poster_img").val();
        $("#poster_img_name").val(filename);
        filename = filename.substring(filename.lastIndexOf('\\')+1);
        reader.onload = function(e) {
          $('#img_container').attr('src', e.target.result);
          $('#img_container').hide();
          $('#img_container').fadeIn(500);
          $('.custom-file-label').text(filename);
        }
        reader.readAsDataURL(input.files[0]);
    }
    $(".alert").removeClass("loading").hide();
    }

    $("#poster_img").change(function(event) {
      RecurFadeIn();
      readURL(this);
    });

function RecurFadeIn(){
    FadeInAlert("Wait for it...");
}

function FadeInAlert(text){
    $(".alert").show();
    $(".alert").text(text).addClass("loading");
}