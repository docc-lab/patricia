package edu.harvard.pass.parser;


import swig.direct.CPLDirect.*;

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

import java.util.Vector;

import com.google.gson.Gson;

/**
 * A provenance object
 *
 * @author Peter Macko
 */
public class PatriciaObject {

        /// The null object
        private static cpl_id_t nullId = null;

        /// Data flow type: Generic
        public static final int DATA_GENERIC = CPLDirectConstants.CPL_DATA_GENERIC;

        /// Data flow type: Generic
        public static final int DATA_INPUT = CPLDirectConstants.CPL_DATA_INPUT;

        /// Data flow type: IPC
        public static final int DATA_IPC = CPLDirectConstants.CPL_DATA_IPC;

        /// Data flow type: Translation
        public static final int DATA_TRANSLATION
                = CPLDirectConstants.CPL_DATA_TRANSLATION;

																								         /// Data flow type: Copy
        public static final int DATA_COPY = CPLDirectConstants.CPL_DATA_COPY;

        /// Control flow type: Generic
        public static final int CONTROL_GENERIC=CPLDirectConstants.CPL_CONTROL_GENERIC;

        /// Control flow type: Generic
        public static final int CONTROL_OP = CPLDirectConstants.CPL_CONTROL_OP;

        /// Control flow type: Start
        public static final int CONTROL_START=CPLDirectConstants.CPL_CONTROL_START;

        /// Version dependency: Generic
        public static final int VERSION_GENERIC=CPLDirectConstants.CPL_VERSION_GENERIC;

        /// Version dependency: Previous version
        public static final int VERSION_PREV = CPLDirectConstants.CPL_VERSION_PREV;

        /// Traversal direction: Ancestors
        public static final int D_ANCESTORS = CPLDirectConstants.CPL_D_ANCESTORS;

        /// Traversal direction: Descendants
        public static final int D_DESCENDANTS=CPLDirectConstants.CPL_D_DESCENDANTS;

        /// Traversal option: No prev/next version edges
        public static final int A_NO_PREV_NEXT_VERSION
                = CPLDirectConstants.CPL_A_NO_PREV_NEXT_VERSION;

        /// Traversal option: No data dependencies
        public static final int A_NO_DATA_DEPENDENCIES
                = CPLDirectConstants.CPL_A_NO_DATA_DEPENDENCIES;

        /// Traversal option: No control dependencies
        public static final int A_NO_CONTROL_DEPENDENCIES
                = CPLDirectConstants.CPL_A_NO_CONTROL_DEPENDENCIES;

        /// Specify all versions where supported
        public static final int ALL_VERSIONS = -1;

        /// The internal object ID
        // cpl_id_t id;
	public String id;

        /// The object originator (cache)
        public String originator = null;

	        /// The object name (cache)
        public String name = null;

        /// The object type (cache)
        public String type = null;

        /// The object containter (cache)
        private CPLObjectVersion container = null;

        /// Whether we know the container
        private boolean knowContainer = false;

        /// The creation time (cache)
        private long creationTime = 0;

	private int version = 0;
        /// The creation session (cache)
        //private CPLSession creationSession = null;

        /// Whether the object creation information is known
        private boolean knowCreationInfo = false;

	public PatriciaObject(String originator, String name, String type, String id) {

                this.originator = originator;
                this.name = name;
                this.type = type;
		
		this.id = id;
		//this.id = CPLDirect.new_cpl_id_tp();
                //this.id.setHi(id.getHi());
                //this.id.setLo(id.getLo());
        }

	public PatriciaObject(String id) {
                this.originator = originator;
                this.name = name;
                this.type = type;
                this.id = id;
        }


	public void setInfo(long ct, int version) {
                this.creationTime = ct;
		this.version = version;
        }

        public long getCreationTime() {
                return creationTime;
        }

	public String getOriginator() {
		return this.originator;
	}

	public String getName() {
                return this.name;
        }

	public String getType() {
                return this.type;
        }

	 /**
         * Query the ancestry of the object
         *
         * @param version a specific version, or ALL_VERSIONS for all versions
         * @param direction the direction, either D_ANCESTORS or D_DESCENDANTS
         * @param flags a combination of A_* flags, or 0 for defaults
         * @return a vector of results &ndash; instances of CPLAncestryEntry
         * @see CPLAncestryEntry
         */
        public Vector<PatriciaAncestryEntry> getAncestry(int version, int direction,
                        int flags) {
	       Vector<PatriciaAncestryEntry> result = new Vector<PatriciaAncestryEntry>();
	       String line2 = "";
	       try {

                      HttpClient client = new DefaultHttpClient();
		      URIBuilder builder = new URIBuilder("http://127.0.0.1:5001/api/patricia/ancestry");
		      builder.setParameter("originator", this.originator).setParameter("name", this.name).setParameter("otype", this.type).
			      setParameter("version", Integer.toString(version)).setParameter("direction", Integer.toString(direction)).setParameter("flags", Integer.toString(flags));

		      HttpGet request = new HttpGet(builder.build());
		      HttpResponse response = client.execute(request);

		      BufferedReader rd = new BufferedReader (new InputStreamReader(response.getEntity().getContent()));
		      String line = "";
		      while ((line = rd.readLine()) != null) {
			      line2 += line;
		      }
		       
		      //System.out.println("size: " + line2.length() + ", " + line2); 
		      if (line2.equals("\"[]\"")) {
			return result;
		      }
		} catch(Exception em) {
                        System.out.println("caught in main.");
                        System.out.println(em.getMessage());
                }

	
	        String[] ancestries = line2.replace("[", "").replace("]","").replace("\"","").split("}");
		String ancestry_info; 
		for(int j=0;j<ancestries.length;j++) 
		{
			ancestry_info = ancestries[j].replace(", {", "").replace("{", "");
			String fields[] = ancestry_info.split(",");
			String other_id="", base_id="", other_name = "", other_type = "", other_originator = "";
			int type = 0, other_version = 0, base_version = 0; 
			boolean dir = true;

			for(int i=0;i<fields.length;i++)
			{
				String[] keyval = fields[i].split(": ");
				keyval[0] = keyval[0].replace(" ", "");
				
				if (keyval[0].equals("base")) {
				
					base_id = keyval[1].split("-")[0];
					base_version = Integer.parseInt(keyval[1].split("-")[1]);

				} else if (keyval[0].equals("direction")) {
					if (keyval[1].equals("ancestor")){
						dir = true;
					} else {
						dir = false;
					}
				//	System.out.println("direction:"+dir);

				} else if (keyval[0].equals("type")) {

					if (keyval[1].equals("data")) {
						type = 1;
					} else if (keyval[1].equals("control")) {
						type = 2;
					}else if (keyval[1].equals("version")) {
						type = 3;
					} else {
						type = 0;
					}
				//	System.out.println("type:"+type);

				} else if (keyval[0].equals("other")) {
					other_id = keyval[1].split("-")[0];
					other_version = Integer.parseInt(keyval[1].split("-")[1]);
				//	System.out.println("other_id:" + other_id + "," + other_version);

				} else if (keyval[0].equals("other_originator")) {
                                        other_originator = keyval[1];
                                //      System.out.println("other_id:" + other_id + "," + other_version);

                                } else if (keyval[0].equals("other_name")) {
                                        other_name = keyval[1];
                                //      System.out.println("other_id:" + other_id + "," + other_version);

                                } else if (keyval[0].equals("other_type")) {
                                        other_type = keyval[1];
                                //      System.out.println("other_id:" + other_id + "," + other_version);

                                } else {
					System.out.println("Property is not supported: " + keyval[0]);
				}
			}	
				
			result.add(new PatriciaAncestryEntry(new PatriciaObjectVersion(this, base_version),
					new PatriciaObjectVersion(new PatriciaObject(other_id),
						other_version),
					type,
					dir));

		}

		System.out.println("Ancestory size for version " + version + " is " + result.size());
		return result;
	}


	/**
         * Get the current version of the object
         *
         * @return the current version
         */
        public int getVersion() {
		try {

                      HttpClient client = new DefaultHttpClient();
                      URIBuilder builder = new URIBuilder("http://127.0.0.1:5001/api/patricia/version");
                      builder.setParameter("originator", this.originator).setParameter("name", this.name).setParameter("otype", this.type);

                      HttpGet request = new HttpGet(builder.build());
                      HttpResponse response = client.execute(request);

                      BufferedReader rd = new BufferedReader (new InputStreamReader(response.getEntity().getContent()));
                      String line = "";
                      String line2 = line;
                      while ((line = rd.readLine()) != null) {
                              line2 += line;
                      }
		      String[] obj_info = line2.replace("{", "").replace("}","").replace("\"", "").split(",");
                      int version=0;
                      for(int i=0;i<obj_info.length;i++)
                      {
                              String[] keyval = obj_info[i].split(": ");
                              keyval[0] = keyval[0].replace(" ", "");
                              keyval[1] = keyval[1].replace(" ", "");
                              if (keyval[0].equals("version")) {
                                      version = Integer.parseInt(keyval[1]);
                              } else {
                                      System.out.println("Property is not supported");
                              }
                      }
		 } catch(Exception em){
                        System.out.println("caught in main.");
                        System.out.println(em.getMessage());
                }

		return version;
        }

	        /**
         * Get the properties of an object
         *
         * @param version the project version or ALL_VERSIONS
         * @param key the property name or null for all entries
         * @return the vector of property entries
         */
        Vector<PatriciaPropertyEntry> getProperties(int version, String key) {

                Vector<PatriciaPropertyEntry> result = new Vector<PatriciaPropertyEntry>();
		try {

                      HttpClient client = new DefaultHttpClient();
                      URIBuilder builder = new URIBuilder("http://127.0.0.1:5001/api/patricia/propery");
                      builder.setParameter("originator", this.originator).setParameter("name", this.name)
			      .setParameter("otype", this.type).setParameter("key", key).setParameter("version", Integer.toString(version));

                      HttpGet request = new HttpGet(builder.build());
                      HttpResponse response = client.execute(request);

                      BufferedReader rd = new BufferedReader (new InputStreamReader(response.getEntity().getContent()));
                      String line = "";
                      String line2 = line;
                      while ((line = rd.readLine()) != null) {
                              line2 += line;
                      }
                      String[] obj_info = line2.replace("{", "").replace("}","").replace("\"", "").split(",");
                      String value = "";
                      for(int i=0;i<obj_info.length;i++)
                      {
                              String[] keyval = obj_info[i].split(": ");
                              keyval[0] = keyval[0].replace(" ", "");
                              keyval[1] = keyval[1].replace(" ", "");
                              if (keyval[0].equals(key)) {
                                      value = keyval[1];
                              } else {
                                      System.out.println("Property is not supported");
                              }
                      }
                 } catch(Exception em){
                        System.out.println("caught in main.");
                        System.out.println(em.getMessage());
                }




                return result;
        }

	    /**
         * Get all properties of an object
         *
         * @return the vector of property entries
         */
        public Vector<PatriciaPropertyEntry> getProperties() {
                return getProperties(ALL_VERSIONS, null);
        }


        /**
         * Get properties of an object associated with the given key
         *
         * @param key the property name (key) or null for all keys
         * @return the vector of property entries
         */
        public Vector<PatriciaPropertyEntry> getProperties(String key) {
                return getProperties(ALL_VERSIONS, key);
        }

	/**
         * Get a specific version of the object
         *
         * @param version the version number
         * @return the specific version of the object
         */
        public PatriciaObjectVersion getSpecificVersion(int version) {
                return new PatriciaObjectVersion(this, version);
        }

}
