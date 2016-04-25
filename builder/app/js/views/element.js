
FormBuilderManager.Views.Element = Backbone.View.extend({
  //tagName: 'li',
  template: _.template($('#formbuilder-input-element').html()),

   initialize: function() {
    
  },

  render: function() {
    var html = this.template(this.model.toJSON());
    this.$el.append(html);
    return this;
  }

 

});
