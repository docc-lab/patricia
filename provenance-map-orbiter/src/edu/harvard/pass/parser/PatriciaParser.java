/*
 * Provenance Aware Storage System - Java Utilities
 *
 * Copyright 2012
 *      The President and Fellows of Harvard College.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the University nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE UNIVERSITY AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE UNIVERSITY OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 */

package edu.harvard.pass.parser;

import java.awt.BorderLayout;
import java.awt.Component;
import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.net.URI;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Vector;

import javax.swing.AbstractListModel;
import javax.swing.BorderFactory;
import javax.swing.DefaultListCellRenderer;
import javax.swing.JButton;
import javax.swing.JFileChooser;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextField;

import edu.harvard.pass.PMeta;
import edu.harvard.pass.cpl.CPLId;
import edu.harvard.pass.cpl.CPL;
import edu.harvard.pass.cpl.CPLAncestryEntry;
import edu.harvard.pass.cpl.CPLException;
import edu.harvard.pass.cpl.CPLFile;
import edu.harvard.pass.cpl.CPLObject;
import edu.harvard.pass.cpl.CPLObjectVersion;
import edu.harvard.pass.cpl.CPLPropertyEntry;
import edu.harvard.util.ParserException;
import edu.harvard.util.ParserFormatException;
import edu.harvard.util.Utils;
import edu.harvard.util.gui.HasWizardPanelConfigGUI;
import edu.harvard.util.gui.WizardPanel;


import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import org.apache.http.HttpResponse;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.DefaultHttpClient;
import org.apache.http.client.utils.URIBuilder;

import edu.harvard.pass.parser.PatriciaObject;


/**
 * A parser for CPL objects
 * 
 * @author Peter Macko
 */
public class PatriciaParser implements Parser, HasWizardPanelConfigGUI {
	
	/// Originator
	protected String originator;
	
	/// Name
	protected String name;
	
	/// Type
	protected String type;
	
	/// The main CPL object
	protected PatriciaObject object;
	
	/// List of matching CPL objects
	//protected Vector<CPLObject> matchingObjects;

	protected Vector<PatriciaObject> matchingObjects;
	
	
	/**
	 * Create an instance of class PatriciaParser
	 */
	public PatriciaParser() {
		object = null;
		matchingObjects = null;
	}
	
	
	/**
	 * Initialize the parser given an input URI. If the file has an ambiguous type (such as *.xml),
	 * the method should check whether the file has a proper format that can be handled by the parser.
	 * 
	 * @param uri the input URI
	 * @throws ParserException on error
	 * @throws ParserFormatException if the file does not have the appropriate format
	 */
	public void initialize(URI uri) throws ParserException {
		
		if (!"cpl".equals(uri.getScheme())) throw new ParserFormatException();
	}
	

	/**
	 * Get a configuration GUI for the parser 
	 * 
	 * @return a list of WizardPanel's for the GUI configuration, or null if not necessary
	 */
	public List<WizardPanel> createConfigurationGUI() {
		
		List<WizardPanel> r = new Vector<WizardPanel>();
		
		r.add(new AttachPanel());
		r.add(new OpenObjectPanel());
		r.add(new ChooseObjectPanel());
		
		return r;
	}
	
	
	/**
	 * Traverse the provenance graph recursively in one direction
	 * 
	 * @param object the object
	 * @param direction the direction
	 * @param nodes the nodes
	 * @param edges the edges
	 */
	protected void fetchAncestry(PatriciaObject object, int direction,
			HashSet<PatriciaObjectVersion> nodes, Vector<PatriciaAncestryEntry> edges) {
		
		LinkedList<PatriciaObjectVersion> next = new LinkedList<PatriciaObjectVersion>();
		for (int i = 0; i <= object.getVersion(); i++) {
			System.out.println(i);
			PatriciaObjectVersion p = object.getSpecificVersion(i);
			nodes.add(p);
			next.add(p);
		}

		System.out.println("Next size is: " + next.size());
		while (!next.isEmpty()) {
			PatriciaObjectVersion n = next.removeFirst();
			
			Vector<PatriciaAncestryEntry> r = n.getAncestry(direction, 0);
			for (PatriciaAncestryEntry e : r) {
				edges.add(e);
				PatriciaObjectVersion p = e.getOther();
				if (!nodes.contains(p)) {
					nodes.add(p);
					next.addLast(p);
				}
			}
		}
	}
	

	/**
	 * Parse an object identified by the given URI
	 * 
	 * @param uri the input URI
	 * @param handler the callback for parser events
	 * @throws ParserException on error
	 */
	public void parse(URI uri, ParserHandler handler) throws ParserException {
		
		if (!"cpl".equals(uri.getScheme())) throw new ParserFormatException();
		
		
		//// Get the ancestry of each object
		HashSet<PatriciaObjectVersion> nodes = new HashSet<PatriciaObjectVersion>();
		Vector<PatriciaAncestryEntry> edges = new Vector<PatriciaAncestryEntry>();
		
		fetchAncestry(object, CPLObject.D_ANCESTORS, nodes, edges);
		fetchAncestry(object, CPLObject.D_DESCENDANTS, nodes, edges);
	
		
		//
		//// Get the set of objects and the set of ver. 0 objects with no ancestry
		//
		HashSet<PatriciaObject> objects = new HashSet<PatriciaObject>();
		HashSet<PatriciaObject> objectsZero = new HashSet<PatriciaObject>();
		for (PatriciaObjectVersion n : nodes) {
			objects.add(n.getObject());
			if (n.getVersion() == 0) objectsZero.add(n.getObject());
		}
		
		for (PatriciaAncestryEntry e : edges) {
			if (e.isVersionDependency()) continue;
			if (e.getAncestor().getVersion() == 0) objectsZero.remove(e.getAncestor().getObject());
			if (e.getDescendant().getVersion() == 0) objectsZero.remove(e.getDescendant().getObject());
		}
		
	        	
		// Turn it into a provenance graph
		
		handler.setMeta(PMeta.CPL());
		handler.beginParsing();
		
		
		// Turn it into a provenance graph: Nodes and node properties
		
		HashMap<String, Integer> idToIndex = new HashMap<String, Integer>();
		
		for (PatriciaObjectVersion n : nodes) {
			
			System.out.println(n.getObject().toString());
			if (!idToIndex.containsKey(n.getObject().toString())) {
				idToIndex.put(n.getObject().toString(), idToIndex.size() + 1);
			}
			
			String id = "" + idToIndex.get(n.getObject().toString()) + "." + n.getVersion();
			if (n.getVersion() == 0) {
				handler.loadTripleAttribute(id, "ORIGINATOR", n.getObject().getOriginator());
				handler.loadTripleAttribute(id, "NAME", n.getObject().getName());
				handler.loadTripleAttribute(id, "TYPE", n.getObject().getType());
			}
			
			//handler.loadTripleAttribute(id, "TIME", "" + n.getCreationTime());
			//if (n.getVersion() == 0 && objectsZero.contains(n.getObject())) {
			//	handler.loadTripleAttribute(id, "TIME", "" + n.getCreationTime());
			//	continue;
			//}
			
			handler.loadTripleAttribute(id, "ID", "" + n.getObject());
			
			String time = "" + n.getCreationTime();
			String label = n.getObject().getName();
	/*		for (int v = 0; v <= n.getVersion(); v++) {
				for (PatriciaPropertyEntry p : n.getObject().getSpecificVersion(v).getProperties()) {
					String key = p.getKey();
					if (key.equalsIgnoreCase("NAME")
							|| key.equalsIgnoreCase("TYPE")
							|| key.equalsIgnoreCase("ORIGINATOR")
							|| key.equalsIgnoreCase("TIME")
							|| key.equalsIgnoreCase("LABEL")) {


						if (key.equalsIgnoreCase("TIME")) {
							time = p.getValue();
							System.out.print("Mania:" + time + "\n");
						}
						if (key.equalsIgnoreCase("LABEL")) {
							label = p.getValue();
							System.out.print("Mania:" + label + "\n"); 
						}
						key = "Custom:" + key;
					}
					handler.loadTripleAttribute(id, key, p.getValue());
				}
			}*/
                        
			handler.loadTripleAttribute(id, "TIME", time);
			if (n.getVersion() == 0 && objectsZero.contains(n.getObject())) continue;

			/*if (n.getObject().getOriginator().equals("/fs")
					&& n.getObject().getType().equals("FILE")) {
				try {
					label = (new File(n.getObject().getName())).getName();
				}
				catch (Exception e) {}
			}*/
			handler.loadTripleAttribute(id, "LABEL", label + " [v. " + n.getVersion() + "]");
		}
		
		
		// Turn it into a provenance graph: Edges and edge labels
		
		for (PatriciaAncestryEntry e : edges) {
			if (e.isVersionDependency() 
					&& e.getAncestor().getVersion() == 0
					&& objectsZero.contains(e.getAncestor().getObject())) continue;
			
			String s_edge = "INPUT";
			if (e.isDataDependency()) {
				switch (e.getType()) {
				case CPLObject.DATA_INPUT:
					s_edge = "INPUT";
					break;
				case CPLObject.DATA_IPC:
					s_edge = "IPC";
					break;
				case CPLObject.DATA_COPY:
					s_edge = "COPY";
					break;
				case CPLObject.DATA_TRANSLATION:
					s_edge = "TRANSLATION";
					break;
				default:
					s_edge = "INPUT";
					break;
				}
			}
			if (e.isControlDependency()) {
				switch (e.getType()) {
				case CPLObject.CONTROL_OP:
					s_edge = "OP";
					break;
				case CPLObject.CONTROL_START:
					s_edge = "START";
					break;
				default:
					s_edge = "OP";
					break;
				}
			}
			if (e.isVersionDependency()) {
				switch (e.getType()) {
				case CPLObject.VERSION_PREV:
					s_edge = "VERSION";
					break;
				default:
					s_edge = "VERSION";
					break;
				}
			}
			
			handler.loadTripleAncestry(
					"" + idToIndex.get(e.getDescendant().getObject().toString()) + "." + e.getDescendant().getVersion(),
					s_edge, 
					"" + idToIndex.get(e.getAncestor().getObject().toString()) + "." + e.getAncestor().getVersion());
		}
		
		
		// Turn it into a provenance graph: Finish
               
		handler.endParsing();
	}
	
	
	/**
	 * Determine whether the parser accepts the given URI
	 * 
	 * @param uri the input URI
	 * @return true if it accepts the input
	 */
	public boolean accepts(URI uri) {
		
		if (!"cpl".equals(uri.getScheme())) return false;
		return true;
	}
	
	
	// Static fields for AttachPanel
	
	private static String lastODBC = "DSN=CPL;";
	
	
	/**
	 * Configuration panel - attach to CPL
	 */
	private class AttachPanel extends WizardPanel implements ActionListener {
		
		private JLabel topLabel;
		private JLabel odbcLabel;
		private JTextField odbcField;
		
		
		/**
		 * Create an instance of AttachPanel
		 */
		public AttachPanel() {
			super("Attach to CPL");


			// Initialize the panel

			panel.setLayout(new GridBagLayout());
			GridBagConstraints c = new GridBagConstraints();

			int gridy = 0;


			// Header

			topLabel = new JLabel("Please input the CPL attachment settings:");
			topLabel.setBorder(BorderFactory.createEmptyBorder(10, 0, 0, 0));
			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 0;
			c.gridy = gridy;
			c.gridwidth = 2;
			c.weightx = 1;
			c.weighty = 0;
			panel.add(topLabel, c);
			c.weightx = 0;
			c.gridwidth = 1;

			gridy++;

			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 0;
			c.gridy = gridy;
			c.gridwidth = 2;
			panel.add(new JLabel(" "), c);
			c.gridwidth = 1;

			gridy++;


			// Object originator

			odbcLabel = new JLabel("ODBC Connection String:   ");
			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 0;
			c.gridy = gridy;
			panel.add(odbcLabel, c);

			odbcField = new JTextField(lastODBC);
			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 1;
			c.gridy = gridy;
			panel.add(odbcField, c);

			gridy++;


			// Finish

			c.fill = GridBagConstraints.BOTH;
			c.gridx = 0;
			c.gridy = gridy;
			c.gridwidth = 2;
			c.weighty = 1;
			panel.add(new JLabel(" "), c);
			c.gridwidth = 1;

			gridy++;

			updateEnabled();
		}


		/**
		 * Callback for when the next button was clicked
		 */
		protected void wizardNext() {
			
			lastODBC = odbcField.getText();
			
			try {
				CPL.detach();
				CPL.attachODBC(odbcField.getText());
			}
			catch (CPLException e) {
				JOptionPane.showMessageDialog(getPanel(), e.getMessage(),
						"CPL Error", JOptionPane.ERROR_MESSAGE);
				cancelNext();
			}
		}


		/**
		 * Update the enabled properties
		 */
		private void updateEnabled() {
		}


		/**
		 * A callback for when an action has been performed
		 * 
		 * @param e the action event
		 */
		@Override
		public void actionPerformed(ActionEvent e) {
			updateEnabled();
		}
	}
	
	
	// Static fields for OpenObjectPanel
	
	private static String lastOriginator = "";
	private static String lastName = "";
	private static String lastType = "";
	private static File lastChosenFile = null;
	
	
	/**
	 * Configuration panel - select an object
	 */
	private class OpenObjectPanel extends WizardPanel implements ActionListener {
		
		private JLabel topLabel;
		private JLabel originatorLabel;
		private JTextField originatorField;
		private JLabel nameLabel;
		private JTextField nameField;
		private JLabel typeLabel;
		private JTextField typeField;
		private JLabel buttonsLabel;
		private JPanel buttonsPanel;
		private JButton fileButton;
		
		
		/**
		 * Create an instance of OpenObjectPanel
		 */
		public OpenObjectPanel() {
			super("Specify a CPL Object");


			// Initialize the panel

			panel.setLayout(new GridBagLayout());
			GridBagConstraints c = new GridBagConstraints();

			int gridy = 0;


			// Header

			topLabel = new JLabel("Please input the CPL object reference:");
			topLabel.setBorder(BorderFactory.createEmptyBorder(10, 0, 0, 0));
			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 0;
			c.gridy = gridy;
			c.gridwidth = 2;
			c.weightx = 1;
			c.weighty = 0;
			panel.add(topLabel, c);
			c.weightx = 0;
			c.gridwidth = 1;

			gridy++;

			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 0;
			c.gridy = gridy;
			c.gridwidth = 2;
			panel.add(new JLabel(" "), c);
			c.gridwidth = 1;

			gridy++;


			// Object originator

			originatorLabel = new JLabel("Originator (namespace):   ");
			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 0;
			c.gridy = gridy;
			panel.add(originatorLabel, c);

			originatorField = new JTextField(lastOriginator);
			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 1;
			c.gridy = gridy;
			panel.add(originatorField, c);

			gridy++;


			// Object names

			nameLabel = new JLabel("Object name:   ");
			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 0;
			c.gridy = gridy;
			panel.add(nameLabel, c);

			nameField = new JTextField(lastName);
			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 1;
			c.gridy = gridy;
			panel.add(nameField, c);

			gridy++;


			// Object types

			typeLabel = new JLabel("Object type:   ");
			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 0;
			c.gridy = gridy;
			panel.add(typeLabel, c);

			typeField = new JTextField(lastType);
			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 1;
			c.gridy = gridy;
			panel.add(typeField, c);

			gridy++;
			
			
			// File button

			buttonsLabel = new JLabel("Or load:   ");
			buttonsLabel.setBorder(BorderFactory.createEmptyBorder(10, 0, 0, 0));
			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 0;
			c.gridy = gridy;
			panel.add(buttonsLabel, c);
			
			buttonsPanel = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
			buttonsPanel.setBorder(BorderFactory.createEmptyBorder(10, 0, 0, 0));
			c.fill = GridBagConstraints.HORIZONTAL;
			c.gridx = 1;
			c.gridy = gridy;
			panel.add(buttonsPanel, c);

			fileButton = new JButton("File...");
			fileButton.addActionListener(this);
			buttonsPanel.add(fileButton);

			gridy++;


			// Finish

			c.fill = GridBagConstraints.BOTH;
			c.gridx = 0;
			c.gridy = gridy;
			c.gridwidth = 2;
			c.weighty = 1;
			panel.add(new JLabel(" "), c);
			c.gridwidth = 1;

			gridy++;

			updateEnabled();
		}

		/**
		 * Patricia: Create a REST API query to CPL
		 */
		protected Vector<PatriciaObject> cplLookup(String originator, String name,
                        String type) {
			Vector<PatriciaObject> r = new Vector<PatriciaObject>(); 	
			   try
			   { 
				   HttpClient client = new DefaultHttpClient();
				   URIBuilder builder = new URIBuilder("http://127.0.0.1:5001/api/patricia");
				   builder.setParameter("originator", originator).setParameter("name", name).setParameter("otype", type);

				   HttpGet request = new HttpGet(builder.build());
				   HttpResponse response = client.execute(request);
				   
				   BufferedReader rd = new BufferedReader (new InputStreamReader(response.getEntity().getContent()));
				   String line = "";
				   String line2 = line;
				   while ((line = rd.readLine()) != null) {
					   line2 += line;
				   }
				   String[] obj_info = line2.replace("[{", "").replace("}]","").replace("\"", "").split(",");
				   String _originator="", _id="", _name = "", _type = "", _version="", _ct="";
				   
				   for(int i=0;i<obj_info.length;i++)
				   {
					   String[] keyval = obj_info[i].split(": ");
					   keyval[0] = keyval[0].replace(" ", "");
					  
					   if (keyval[0].equals("originator")) {
						System.out.println(keyval[1]);
						_originator = keyval[1];
					   } else if (keyval[0].equals("id")) {
					        System.out.println(keyval[1]);
						_id  = keyval[1];
					   } else if (keyval[0].equals("type")) {
				         	System.out.println(keyval[1]);
						_type = keyval[1];
                                           } else if (keyval[0].equals("name")) {
						System.out.println(keyval[1]);
						_name = keyval[1];
                                           } else if (keyval[0].equals("version")) {
                                                System.out.println(keyval[1]);
                                                _version = keyval[1];
                                           } else if (keyval[0].equals("ct")) {
                                                System.out.println(keyval[1]);
                                                _ct = keyval[1];
                                           } else {
					        System.out.println("Property is not supported");
                                           }
				   }


				   PatriciaObject o = new PatriciaObject(_originator, _name, _type, _id);
				   o.setInfo(Long.parseLong(_ct), Integer.parseInt(_version));

                                   r.add(o);				   

				   //JSONParser parser = new JSONParser();
				   //Object obj = parser.parse(line2);
				   //JSONArray array = (JSONArray)obj;
			   
			   } catch(Exception em){ 
				   System.out.println("caught in main.");
				   System.out.println(em.getMessage());
			   } 

			return r; 
		}

		/**
		 * Callback for when the next button was clicked
		 */
		protected void wizardNext() {
			
			originator = originatorField.getText();
			name = nameField.getText();
			type = typeField.getText();		
			
			lastOriginator = originatorField.getText();
			lastName = nameField.getText();
			lastType = typeField.getText();
			
			try {
				/*send restful query to the 127.0.0.1:5000/lookup */
				matchingObjects = cplLookup(originator, name, type);
				//matchingObjects = CPLObject.lookupAll(originator, name, type);
			}
			catch (CPLException e) {
				JOptionPane.showMessageDialog(getPanel(), e.getMessage(),
						"CPL Error", JOptionPane.ERROR_MESSAGE);
				cancelNext();
			}
		}

		/**
		 * Update the enabled properties
		 */
		private void updateEnabled() {
		}

		/**
		 * A callback for when an action has been performed
		 * 
		 * @param e the action event
		 */
		@Override
		public void actionPerformed(ActionEvent e) {
			
			if (e.getSource() == fileButton) {
				JFileChooser fc = new JFileChooser();
				fc.setDialogTitle(title);
				fc.setDialogType(JFileChooser.OPEN_DIALOG);
				if (lastChosenFile != null) fc.setSelectedFile(lastChosenFile);
				int r = fc.showOpenDialog(getWizard());
				if (r != JFileChooser.APPROVE_OPTION) return;
				lastChosenFile = fc.getSelectedFile();
				
				CPLFile f = null;
				try {
					f = CPLFile.lookup(lastChosenFile);
				}
				catch (CPLException ex) {
					String msg = ex.getMessage();
					if (msg.equalsIgnoreCase("not found") || msg.equalsIgnoreCase("not found.")) {
						msg = "The selected file does not have any attached provenance information.";
					}
					JOptionPane.showMessageDialog(getPanel(), msg,
							"CPL Error", JOptionPane.ERROR_MESSAGE);
					return;
				}
				
				originatorField.setText(f.getOriginator());
				nameField.setText(f.getName());
				typeField.setText(f.getType());
			}
			
			updateEnabled();
		}
	}
	
	
	/**
	 * Configuration panel - choose an object from a list of matching objects
	 */
	private class ChooseObjectPanel extends WizardPanel implements ActionListener {
		
		private JLabel topLabel;
		private JScrollPane objectListScroll;
		private PatriciaObjectListModel objectListModel;
		private JList objectList;
		
		
		/**
		 * Create an instance of ChooseObjectPanel
		 */
		public ChooseObjectPanel() {
			super("Choose a Patricia Object");


			// Initialize the panel

			panel.setLayout(new BorderLayout());


			// Header

			topLabel = new JLabel("Choose an object from the following matches:");
			topLabel.setBorder(BorderFactory.createEmptyBorder(10, 0, 0, 0));
			panel.add(topLabel, BorderLayout.NORTH);
			
			
			// List of objects
			
			objectListModel = new PatriciaObjectListModel();
			objectList = new JList(objectListModel);
			objectList.setCellRenderer(new PatriciaObjectCellRenderer());
			
			objectListScroll = new JScrollPane(objectList);
			panel.add(objectListScroll, BorderLayout.CENTER);
			

			// Finish

			updateEnabled();
		}
		
		
		/**
		 * Prepare the panel to be displayed (this is a callback
		 * for just before the wizard panel is displayed)
		 */
		protected void prepare() {
			
			Collections.sort(matchingObjects, new Comparator<PatriciaObject>() {
				@Override
				public int compare(PatriciaObject a, PatriciaObject b) {
					if (a.getCreationTime() > b.getCreationTime()) return -1;
					if (a.getCreationTime() < b.getCreationTime()) return -1;
					return a.toString().compareTo(b.toString());
				}
			});
			
			objectListModel.setData(matchingObjects);
			
			if (matchingObjects.size() > 0) objectList.setSelectedIndex(0);
		}


		/**
		 * Callback for when the next button was clicked
		 */
		protected void wizardNext() {
			
			Object selectedObject = objectList.getSelectedValue();
			if (selectedObject == null) {
				JOptionPane.showMessageDialog(getPanel(), "Please first select an object",
						"CPL Error", JOptionPane.ERROR_MESSAGE);
				cancelNext();
				return;
			}
			
			if (!(selectedObject instanceof PatriciaObject)) {
				throw new InternalError();
			}
			
			object = (PatriciaObject) selectedObject;
		}


		/**
		 * Update the enabled properties
		 */
		private void updateEnabled() {
		}


		/**
		 * A callback for when an action has been performed
		 * 
		 * @param e the action event
		 */
		@Override
		public void actionPerformed(ActionEvent e) {
			
			updateEnabled();
		}
		
		
		/**
		 * The list model
		 */
		@SuppressWarnings("serial")
		private class PatriciaObjectListModel extends AbstractListModel {
			
			private Vector<PatriciaObject> contents = new Vector<PatriciaObject>();

			
			/**
			 * Get the element at the given index
			 * 
			 * @param index the index
			 * @return the element at the given index
			 */
			@Override
			public Object getElementAt(int index) {
				return contents.get(index);
			}

			
			/**
			 * Get the size of the list
			 * 
			 * @return the size of the list
			 */
			@Override
			public int getSize() {
				return contents.size();
			}
		
			/**	
			 * @param c the new contents
			 */
			public void setData(Vector<PatriciaObject> c) {
				
				int n = contents.size();
				contents.clear();
				if (n > 0) fireIntervalRemoved(this, 0, n - 1);
				
				contents.addAll(c);
				n = contents.size();
				if (n > 0) fireIntervalAdded(this, 0, n - 1);
			}
		}

		
		/**
		 *  The custom cell renderer
		 */
		@SuppressWarnings("serial")
		class PatriciaObjectCellRenderer extends DefaultListCellRenderer {

			/**
			 * Return the cell renderer component
			 */
			public Component getListCellRendererComponent(JList list,
					Object value, // value to display
					int index, // cell index
					boolean iss, // is the cell selected
					boolean chf) // the list and the cell have the focus
			{
				PatriciaObject c = Utils.<PatriciaObject>cast(value);
				
				String label = "";
				label += new java.sql.Date(1000L * c.getCreationTime());
				label += " ";
				label += new java.sql.Time(1000L * c.getCreationTime());

				super.getListCellRendererComponent(list, label, index, iss, chf);
				return this;
			}
		}
	}
}
