/*
 * Provenance Aware Storage System - Java Utilities
 *
 * Copyright 2011
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

import edu.harvard.pass.WithPMeta;
import edu.harvard.util.ParserException;


/**
 * A handler for parser events
 * 
 * @author Peter Macko
 */
public interface ParserHandler extends WithPMeta {
	
	/**
	 * Start loading the graph
	 * 
	 * @throws ParserException on error
	 */
	public void beginParsing() throws ParserException;

	/**
	 * Process an ancestry triple
	 * 
	 * @param s_pnode the string version of a p-node
	 * @param s_edge the string version of an edge
	 * @param s_value the string version of the second p-node
	 * @throws ParserException on error
	 */
	public void loadTripleAncestry(String s_pnode, String s_edge, String s_value) throws ParserException;

	/**
	 * Process an attribute triple
	 * 
	 * @param s_pnode the string version of a p-node
	 * @param s_edge the string version of an edge
	 * @param s_value the string version of a value
	 * @throws ParserException on error
	 */
	public void loadTripleAttribute(String s_pnode, String s_edge, String s_value) throws ParserException;
	
	/**
	 * Finish loading the graph
	 * 
	 * @throws ParserException on error
	 */
	public void endParsing() throws ParserException;
}
