
// model for our form builder. It describes the element added to the form by an user 
FormBuilderManager.Models.Element = Backbone.Model.extend({
  
  defaults: {
  	id: null,
    div_id: null,
  	type: null, // type of the element added, e.g. button, textfield, checkbox etc
  	label: null,
    value: null, // default value of the element
    ondragstart: null

  },

  initialize: function(){
  	//alert("FormBuilderManager.Models.Element");
  }


});
