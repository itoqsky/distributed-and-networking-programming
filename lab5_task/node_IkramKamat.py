from argparse import ArgumentParser
from bisect import bisect_left
from threading import Thread
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer

M = 5
PORT = 1234
RING = [2, 7, 11, 17, 22, 27]


class Node:
    def __init__(self, node_id):
        """Initializes the node properties and constructs the finger table according to the Chord formula"""
        self.finger_table = []

        for i in range(M):
            self.finger_table.append(RING[bisect_left(RING, (node_id + 2 ** i) % (2 ** M)) % 6])

        self.data = {}
        self.id = node_id
        self.successor_id = RING[(RING.index(self.id) + 1) % 6]
        # self.predecessor_id = RING.index(self.id) - 1
        print(f"Node created! Finger table = {self.finger_table}")

    def closest_preceding_node(self, id):
        """Returns node_id of the closest preceeding node (from n.finger_table) for a given id"""
        for i in reversed(self.finger_table):
            if i == RING[-1]:
                if RING[-1] < id or id < RING[0]:
                    return i
            elif i < self.id:
                if i < id < self.id:
                    return i
            else:
                if self.id < i < id:
                    return i
        return self.id

    def find_successor(self, id):
        """Recursive function returning the identifier of the node responsible for a given id"""
        if id == self.id:
            return id

        if self.id < id <= self.successor_id:
            return self.successor_id

        n0 = self.closest_preceding_node(id)

        if n0 == self.id:
            return self.id

        with ServerProxy(f'http://node_{n0}:{PORT}') as node:
            print(f"Forwarding request (key={id}) to node: {n0}")
            return node.find_successor(id)

    def put(self, key, value):
        """Stores the given key-value pair in the node responsible for it"""
        print(f"put({key}, {value})")
        try:
            n0 = self.find_successor(key)
            # print(f'{self.id} {n0}')
            if self.id == n0:
                return self.store_item(key, value)
            with ServerProxy(f'http://node_{n0}:{PORT}') as node:
                return node.store_item(key, value)
        except Exception as e:
            print(e)
            return False

    def get(self, key):
        """Gets the value for a given key from the node responsible for it"""
        print(f"get({key})")
        try:
            n0 = self.find_successor(key)
            if self.id == n0:
                return self.retrieve_item(key)
            with ServerProxy(f'http://node_{n0}:{PORT}') as node:
                return node.retrieve_item(key)
        except Exception as e:
            # print("Error in get() ", e)
            print(e)
            return -1

    def store_item(self, key, value):
        """Stores a key-value pair into the data store of this node"""
        try:
            self.data[key] = value
            return True
        except Exception as e:
            # print("Error in store_item() ", e)
            print(e)
            return False

    def retrieve_item(self, key):
        """Retrieves a value for a given key from the data store of this node"""
        if key in self.data:
            return self.data[key]
        return -1


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('node_id')
    args = parser.parse_args()

    node = Node(int(args.node_id))

    server = SimpleXMLRPCServer(('0.0.0.0', PORT))

    server.register_function(node.find_successor, 'find_successor')
    server.register_function(node.closest_preceding_node, 'closest_preceding_node')
    server.register_function(node.store_item, 'store_item')
    server.register_function(node.retrieve_item, 'retrieve_item')
    server.register_function(node.get, 'get')
    server.register_function(node.put, 'put')

    #Thread(target=server.serve_forever).start()
    server.serve_forever()
