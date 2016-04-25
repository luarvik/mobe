
FormBuilderManager.Views.Elements = Backbone.View.extend({ 

   template: _.template($('#formbuilder-elements').html()), 
   
   renderOne: function(element) {
    
    var itemView = new FormBuilderManager.Views.Element({model: element});
    this.$('.elements-container').append(itemView.render().$el);
  },
  
  render: function() {

    var html = this.template();
    this.$el.html(html);
    
    this.collection.each(this.renderOne, this);
    return this;
  }  

 
});