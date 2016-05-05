
// this is the wrapper class for our form builder
window.FormBuilderManager = {
	Models: {},
	Collections: {},
	Views: {},

    //  The start function. It will be called from the browser
	start: function(data){
		

   

		var elements = new FormBuilderManager.Collections.Elements(data.elements);
    
		var router = new FormBuilderManager.Router();
    
    
     router.on('route:home', function() {

          router.navigate('elements', {
            trigger: true,
            replace: true
      });
    }); 
    
     router.on('route:showElements', function() {
      
      var elementsView = new FormBuilderManager.Views.Elements({
        collection: elements
      });
      
      
      $('.main-container').html(elementsView.render().$el); 
    
    });

   
      
      Backbone.history.start();
   
	},

viewSavedForm: function(data){

  var felements = new FormBuilderManager.Collections.Selements(data.felements);
    
  var felementsView = new FormBuilderManager.Views.Selements({
        collection: felements
      });
  
  $('.fmain-container').html(felementsView.render().$el);     
  
}


};