import random
import sched
import socket
import time
from threading import Thread
from argparse import ArgumentParser
from enum import Enum
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer

PORT = 1234
CLUSTER = [1, 2, 3]
ELECTION_TIMEOUT = (6, 8)
HEARTBEAT_INTERVAL = 5


class NodeState(Enum):
    """Enumerates the three possible node states (follower, candidate, or leader)"""
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3


class Node:
    def __init__(self, node_id):
        """Non-blocking procedure to initialize all node parameters and start the first election timer"""
        self.node_id = node_id
        self.state = NodeState.FOLLOWER
        self.term = 0
        self.votes = {}
        self.voted_for = {}
        self.log = []
        self.pending_entry = ''
        self.sched = sched.scheduler()
        # TODO: start election timer for this node
        self.reset_election_timer()
        print(f"Node started! State: {self.state}. Term: {self.term}")

    def is_leader(self):
        """Returns True if this node is the elected cluster leader and False otherwise"""
        return self.state == NodeState.LEADER

    def reset_election_timer(self):
        """Resets election timer for this (follower or candidate) node and returns it to the follower state"""
        if self.state == NodeState.LEADER:
            return
        if self.sched.queue:
            self.sched.cancel(self.sched.queue[0])
        self.sched.enter(random.uniform(*ELECTION_TIMEOUT), 1, self.hold_election)
        self.state = NodeState.FOLLOWER
        self.votes = {}
        self.voted_for = {}
        return

    def hold_election(self):
        """Called when this follower node is done waiting for a message from a leader (election timeout)
            The node increments term number, becomes a candidate and votes for itself.
            Then call request_vote over RPC for all other online nodes and collects their votes.
            If the node gets the majority of votes, it becomes a leader and starts the hearbeat timer
            If the node loses the election, it returns to the follower state and resets election timer.
        """
        if self.state != NodeState.FOLLOWER:
            return

        self.term += 1 
        self.state = NodeState.CANDIDATE
        print(f"New election term {self.term}. State: {self.state}")

        self.votes[self.node_id] = True
        self.voted_for[self.term] = self.node_id

        unreceived_votes = 0
        for node_id in CLUSTER:
            if node_id != self.node_id:
                try:
                    with ServerProxy(f'http://node_{node_id}:{PORT}') as node:
                        print(f"Requesting vote from node {node_id}")
                        if node.request_vote(self.term, self.node_id):
                            self.votes[node_id] = True
                except socket.error:
                    print(f"Follower node {node_id} is offline")
                    unreceived_votes += 1
        
        received_votes = len(CLUSTER) - unreceived_votes
        print(f"Received {received_votes} votes", end=". ")
        if len(self.votes) > received_votes / 2:
            self.state = NodeState.LEADER
            print("State: Leader")
            self.append_entries()
        else:
            print("State: Follewer")
            self.reset_election_timer()
        return

    def request_vote(self, term, candidate_id):
        """Called remotely when a node requests voting from other nodes.
            Updates the term number if the received one is greater than `self.term`
            A node rejects the vote request if it's a leader or it already voted in this term.
            Returns True and update `self.votes` if the vote is granted to the requester candidate and False otherwise.
        """
        print(f"Got a vote request from node {candidate_id} in term {term}")
        if self.state == NodeState.LEADER or self.term > term:
            print(f"Didn't vote for node {candidate_id} (I'm a Leader)")
            return False
        
        if self.term < term:
            self.term = term
            self.state = NodeState.FOLLOWER
            self.reset_election_timer()
        
        if self.voted_for.get(self.term) != None:
            print(f"Didn't vote for node {candidate_id} (Already voted for {self.voted_for[self.term]})")
            return False
        
        self.voted_for[self.term] = candidate_id
        print(f"Voted for node {self.voted_for[self.term]} in term {self.term}")
        return True

    def append_entries(self):
        """Called by leader every HEARTBEAT_INTERVAL, sends a heartbeat message over RPC to all online followers.
            Accumulates ACKs from followers for a pending log entry (if any)
            If the majority of followers ACKed the entry, the entry is committed to the log and is no longer pending
        """
        if self.state != NodeState.LEADER:
            return
        
        print("Sending heartbeat to followers")
        acks = 1
        for node_id in CLUSTER:
            if node_id != self.node_id:
                try:
                    with ServerProxy(f'http://node_{node_id}:{PORT}') as node:
                        if node.heartbeat(self.pending_entry):
                            self.votes[node_id] = True
                            acks += 1
                except socket.error:
                    print(f"Follower node {node_id} is offline")

        if acks > len(self.votes) / 2:
            if self.pending_entry != '':
                print(f"Leader committed entry '{self.pending_entry}'")
                self.log.append(self.pending_entry)
            self.pending_entry = ''
        else:
            print(f"Failed to commit entry '{self.pending_entry}'")
        self.sched.enter(HEARTBEAT_INTERVAL, 1, self.append_entries)
        return

    def heartbeat(self, leader_entry):
        """Called remotely from the leader to inform followers that it's alive and supply any pending log entry
            Followers would commit an entry if it was pending before, but is no longer now.
            Returns True to ACK the heartbeat and False on any problems.
        """
        print(f"Heartbeat received from leader (entry='{leader_entry}')")
        if self.state== NodeState.LEADER:
            return False
        
        if self.pending_entry != '' and self.pending_entry != leader_entry:
            self.log.append(self.pending_entry)
            print(f"Follower committed entry '{self.pending_entry}'")
        
        self.pending_entry = leader_entry
        self.reset_election_timer()
            
        return True

    def leader_receive_log(self, log):
        """Called remotely from the client. Executed only by the leader upon receiving a new log entry
            Returns True after the entry is committed to the leader log and False on any problems
        """
        if self.state != NodeState.LEADER:
            return False
        
        print(f"Leader received log '{log}' from client")
        self.pending_entry = log
        self.append_entries()
        return True


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("node_id", type=int)
    args = parser.parse_args()

    node = Node(args.node_id)    

    try:
        server = SimpleXMLRPCServer(('0.0.0.0', PORT), allow_none=True, logRequests=False)
        server.register_instance(node)
        rpc_thread = Thread(target=node.sched.run)
        rpc_thread.start()
        server.serve_forever()
    except KeyboardInterrupt:
        node.sched.cancel(node.sched.queue[0]) 
        print("Exiting...")
