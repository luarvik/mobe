FormBuilderManager.Models.Selement = Backbone.Model.extend({
  
  defaults: {
  	id: null,
    div_id: null,
  	type: null, // type of the element added, e.g. button, textfield, checkbox etc
  	label: null,
    value: null, // default value of the element
    style: null

  },

  initialize: function(){
  	//alert("FormBuilderManager.Models.Element");
  }


});