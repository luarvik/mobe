FormBuilderManager.Views.Selements = Backbone.View.extend({ 

   template: _.template($('#formbuilder-felements').html()), 
   
   renderOne: function(element) {
    
    var itemView = new FormBuilderManager.Views.Selement({model: element});
    this.$('.felements-container').append(itemView.render().$el);
  },
  
  render: function() {
 
    var html = this.template();
    this.$el.html(html);
    
    this.collection.each(this.renderOne, this);
    return this;
  }  

 
});