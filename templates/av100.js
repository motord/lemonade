/**
 * Created by PyCharm.
 * User: peter
 * Date: 11/21/11
 * Time: 11:33 PM
 * To change this template use File | Settings | File Templates.
 */
$(function(){

  var $container = $('#container');

  $container.imagesLoaded( function(){
    $container.masonry({
      itemSelector : '.pin',
      gutterWidth: 15
    });
  });

});
