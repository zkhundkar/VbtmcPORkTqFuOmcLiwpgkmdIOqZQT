
### Consolidated Clinical Document (CCD) Renderer

Developed an xslt transform with embedded Javascript and callbacks to a .NET application to render a CCD in a user-friendly format. The transform is largely derived from the [LantanaGroup stylesheets repository](https://github.com/lantanagroup/stylesheets) with these additional features:

1. *Collapsing or expanding* 
   * Each section can be collapsed or expanded by clicking on the header, e.g., any where on the dark blue bar. The click is a toggle, expands a collapsed section or expands a collapsed section. The folder icon changes to a closed folder when collapsed and a open folder when the expanded.  
   * The same toggle function can be invoked by clicking directly on any of the folder icons 
   * All collapsed sections should be listed in the "Collapsed Sections" group in the table of contents on the left. A click on any of the yellow "buttons" here will expand the section 
2. *Hiding*
   * A section can be hidden from the body by clicking on the "X" icon (far right) for any section. 
   * All hidden sections should be listed in the "Hidden Sections" group in the table of contents (red "buttons") 
   * A hidden section will should as italicized in the table of contents 

3. *Unhiding*
   A click on a hidden section (red "button" in the hidden sections group) will restore the section in the main body. It will be restored in its original state (collapsed or expanded) in the order listed in the table of contents 

4. *Sorting*
   * A click on the up arrow icon will move a clinical section above the section immediately preceding it. If the section was the first one, it will remain where it was. When a section is moved to the top, its up arrow should be hidden. 
   * A click on the down arrow icon will move the section down one, I.e., below the immediately following section. If the section was the last clinical section, there will be no change in the order.  When a section becomes the last clinical section. Its down arrow should be hidden 
   * A section maybe moved more easily by clicking and dragging it in the table of contents. The poistion where the mouse is released will be where the section is moved to (within the set of clinical sections 

5. *User preferences* 
   Any sort, expand/collapse or hide/unhide action will enable the "Save View" button. When it is clicked, the current order and set of hidden and collapsed sections are stored as the user's chosen preferences for future views. 




![Sample](https://github.com/zkhundkar/public-portfolio/tree/master/cda-render/ccda_sample.png)
