#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2012 thomasv@ecdsa.org
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.



import os
import util
import bitcoin
from bitcoin import *

#import lyra2re_hash
#import lyra2re2_hash
import fjc_scrypt

MAX_TARGET = 0x00000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF


class Blockchain(util.PrintError):
    '''Manages blockchain headers and their verification'''

    def __init__(self, config, network):
        self.config = config
        self.network = network
        self.checkpoint_height, self.checkpoint_hash = self.get_checkpoint()
        self.check_truncate_headers()
        self.set_local_height()

    def height(self):
        return self.local_height

    def init(self):
        import threading
        if os.path.exists(self.path()):
            self.downloading_headers = False
            return
        self.downloading_headers = True
        t = threading.Thread(target=self.init_headers_file)
        t.daemon = True
        t.start()

    def pass_checkpoint(self, header):
        if type(header) is not dict:
            return False
        if header.get('block_height') != self.checkpoint_height:
            return True
        if header.get('prev_block_hash') is None:
            header['prev_block_hash'] = '00' * 32
        try:
            _hash = self.hash_header(header)
        except:
            return False
        return _hash == self.checkpoint_hash

    def verify_header(self, header, prev_header, bits, target):
        prev_hash = self.hash_header(prev_header)
        _hash = self.hash_header(header)
        _powhash = self.pow_hash_header(header)
        if prev_hash != header.get('prev_block_hash'):
            raise BaseException("prev hash mismatch: %s vs %s" % (prev_hash, header.get('prev_block_hash')))
        if not self.pass_checkpoint(header):
            raise BaseException('failed checkpoint')
        if self.checkpoint_height == header.get('block_height'):
            self.print_error("validated checkpoint", self.checkpoint_height)
        if bitcoin.TESTNET:
            return
        if bits != header.get('bits'):
            raise BaseException("bits mismatch: %s vs %s for height %s" % (bits, header.get('bits'), header.get('block_height')))
        if int('0x' + _powhash, 16) > target:
            raise BaseException("insufficient proof of work: %s vs target %s" % (int('0x' + _powhash, 16), target))

    def verify_chain(self, chain):
        first_header = chain[0]
        prev_header = self.read_header(first_header.get('block_height') - 1)
        for header in chain:
            height = header.get('block_height')
            bits, target = self.get_target(height, chain)
            self.verify_header(header, prev_header, bits, target)
            prev_header = header

    def verify_chunk(self, index, data):
        num = len(data) / 80
        prev_header = None
        if index != 0:
            prev_header = self.read_header(index * 2016 - 1)
        headers = []
        for i in range(num):
            raw_header = data[i * 80:(i + 1) * 80]
            header = self.deserialize_header(raw_header, index * 2016 + i)
            headers.append(header)
            bits, target = self.get_target(index*2016 + i, headers)
            self.verify_header(header, prev_header, bits, target)
            prev_header = header

    def serialize_header(self, res):
        s = int_to_hex(res.get('version'), 4) \
            + rev_hex(res.get('prev_block_hash')) \
            + rev_hex(res.get('merkle_root')) \
            + int_to_hex(int(res.get('timestamp')), 4) \
            + int_to_hex(int(res.get('bits')), 4) \
            + int_to_hex(int(res.get('nonce')), 4)
        return s

    def deserialize_header(self, s, height):
        hex_to_int = lambda s: int('0x' + s[::-1].encode('hex'), 16)
        h = {}
        h['version'] = hex_to_int(s[0:4])
        h['prev_block_hash'] = hash_encode(s[4:36])
        h['merkle_root'] = hash_encode(s[36:68])
        h['timestamp'] = hex_to_int(s[68:72])
        h['bits'] = hex_to_int(s[72:76])
        h['nonce'] = hex_to_int(s[76:80])
        h['block_height'] = height
        return h

    def hash_header(self, header):
        if header is None:
            return '0' * 64
        return hash_encode(Hash(self.serialize_header(header).decode('hex')))

    def pow_hash_header(self, header):
        return rev_hex(fjc_scrypt.getPoWHash(self.serialize_header(header).decode('hex')).encode('hex'))

    def path(self):
        return util.get_headers_path(self.config)

    def init_headers_file(self):
        filename = self.path()
        try:
            import urllib, socket
            socket.setdefaulttimeout(30)
            self.print_error("downloading ", bitcoin.HEADERS_URL)
            urllib.urlretrieve(bitcoin.HEADERS_URL, filename + '.tmp')
            os.rename(filename + '.tmp', filename)
            self.print_error("done.")
        except Exception:
            self.print_error("download failed. creating file", filename)
            open(filename, 'wb+').close()
        self.downloading_headers = False
        self.set_local_height()
        self.print_error("%d blocks" % self.local_height)

    def save_chunk(self, index, chunk):
        filename = self.path()
        f = open(filename, 'rb+')
        f.seek(index * 2016 * 80)
        h = f.write(chunk)
        f.close()
        self.set_local_height()

    def save_header(self, header):
        data = self.serialize_header(header).decode('hex')
        assert len(data) == 80
        height = header.get('block_height')
        filename = self.path()
        f = open(filename, 'rb+')
        f.seek(height * 80)
        h = f.write(data)
        f.close()
        self.set_local_height()

    def set_local_height(self):
        self.local_height = 0
        name = self.path()
        if os.path.exists(name):
            h = os.path.getsize(name) / 80 - 1
            if self.local_height != h:
                self.local_height = h

    def read_header(self, block_height):
        name = self.path()
        if os.path.exists(name):
            f = open(name, 'rb')
            f.seek(block_height * 80)
            h = f.read(80)
            f.close()
            if len(h) == 80:
                h = self.deserialize_header(h, block_height)
                return h

    def BIP9(self, height, flag):
        v = self.read_header(height)['version']
        return ((v & 0xE0000000) == 0x20000000) and ((v & flag) == flag)

    def segwit_support(self, N=576):
        h = self.local_height
        return sum([self.BIP9(h - i, 2) for i in range(N)]) * 10000 / N / 100.

    def check_truncate_headers(self):
        checkpoint = self.read_header(self.checkpoint_height)
        if checkpoint is None:
            return
        if self.hash_header(checkpoint) == self.checkpoint_hash:
            return
        self.print_error('checkpoint mismatch:', self.hash_header(checkpoint), self.checkpoint_hash)
        self.print_error('Truncating headers file at height %d' % self.checkpoint_height)
        name = self.path()
        f = open(name, 'rb+')
        f.seek(self.checkpoint_height * 80)
        f.truncate()
        f.close()

    def convbits(self, new_target):
        c = ("%064x" % new_target)[2:]
        while c[:2] == '00' and len(c) > 6:
            c = c[2:]
        bitsN, bitsBase = len(c) / 2, int('0x' + c[:6], 16)
        if bitsBase >= 0x800000:
            bitsN += 1
            bitsBase >>= 8
        new_bits = bitsN << 24 | bitsBase
        return new_bits
        
    def convbignum(self, bits):
        bitsN = (bits >> 24) & 0xff
        if not (bitsN >= 0x03 and bitsN <= 0x1e):
            raise BaseException("First part of bits should be in [0x03, 0x1e]")
        bitsBase = bits & 0xffffff
        if not (bitsBase >= 0x8000 and bitsBase <= 0x7fffff):
            raise BaseException("Second part of bits should be in [0x8000, 0x7fffff]")
        target = bitsBase << (8 * (bitsN-3))
        return target
        
        
        
    def KimotoGravityWell(self, height, chain=[], data=None):
        # print_msg ("height=",height,"chain=", chain, "data=", data)
        BlocksTargetSpacing = 2.5 * 60  # 2.5 minutes
        TimeDaySeconds = 60 * 60 * 24
        PastSecondsMin = TimeDaySeconds * 0.25
        PastSecondsMax = TimeDaySeconds * 7
        PastBlocksMin = PastSecondsMin / BlocksTargetSpacing
        PastBlocksMax = PastSecondsMax / BlocksTargetSpacing

        BlockReadingIndex = height - 1
        BlockLastSolvedIndex = height - 1
        TargetBlocksSpacingSeconds = BlocksTargetSpacing
        PastRateAdjustmentRatio = 1.0
        bnProofOfWorkLimit = 0x00000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

        if (BlockLastSolvedIndex <= 0 or BlockLastSolvedIndex < PastSecondsMin):
            new_target = bnProofOfWorkLimit
            new_bits = self.convbits(new_target)
            return new_bits, new_target

        last = self.read_header(BlockLastSolvedIndex)
        if last == None:
            for h in chain:
                if h.get('block_height') == BlockLastSolvedIndex:
                    last = h
                    break

        for i in xrange(1, int(PastBlocksMax) + 1):
            PastBlocksMass = i

            reading = self.read_header(BlockReadingIndex)

            if reading == None:
                for h in chain:
                    if h.get('block_height') == BlockReadingIndex:
                        # print_msg("get block from chain")
                        reading = h
                        break

            if (reading == None or last == None):
                raise BaseException("Could not find previous blocks when calculating difficulty reading: "
				+ str(BlockReadingIndex) + ", last: " + str(BlockLastSolvedIndex) + ", height: " + str(height))

            # print_msg ("last=",last)
            if (i == 1):
                print_msg("reading(", BlockReadingIndex, ")=", reading)
                PastDifficultyAverage = self.convbignum(reading.get('bits'))
            else:
                PastDifficultyAverage = float(
                    (self.convbignum(reading.get('bits')) - PastDifficultyAveragePrev) / float(
                        i)) + PastDifficultyAveragePrev

            PastDifficultyAveragePrev = PastDifficultyAverage

            PastRateActualSeconds = last.get('timestamp') - reading.get('timestamp')
            PastRateTargetSeconds = TargetBlocksSpacingSeconds * PastBlocksMass
            PastRateAdjustmentRatio = 1.0
            if (PastRateActualSeconds < 0):
                PastRateActualSeconds = 0.0

            if (PastRateActualSeconds != 0 and PastRateTargetSeconds != 0):
                PastRateAdjustmentRatio = float(PastRateTargetSeconds) / float(PastRateActualSeconds)

            EventHorizonDeviation = 1 + (0.7084 * pow(float(PastBlocksMass) / float(144), -1.228))
            EventHorizonDeviationFast = EventHorizonDeviation
            EventHorizonDeviationSlow = float(1) / float(EventHorizonDeviation)

            # print_msg ("EventHorizonDeviation=",EventHorizonDeviation,"EventHorizonDeviationFast=",EventHorizonDeviationFast,"EventHorizonDeviationSlow=",EventHorizonDeviationSlow )

            if (PastBlocksMass >= PastBlocksMin):

                if ((PastRateAdjustmentRatio <= EventHorizonDeviationSlow) or (
                    PastRateAdjustmentRatio >= EventHorizonDeviationFast)):
                    break

                if (BlockReadingIndex < 1):
                    break

            BlockReadingIndex = BlockReadingIndex - 1
        # print_msg ("BlockReadingIndex=",BlockReadingIndex )


        # print_msg ("for end: PastBlocksMass=",PastBlocksMass )
        bnNew = PastDifficultyAverage
        if (PastRateActualSeconds != 0 and PastRateTargetSeconds != 0):
            bnNew *= float(PastRateActualSeconds)
            bnNew /= float(PastRateTargetSeconds)

        if (bnNew > bnProofOfWorkLimit):
            bnNew = bnProofOfWorkLimit

        # new target
        new_target = bnNew
        new_bits = self.convbits(new_target)

        # print_msg("bits", new_bits , "(", hex(new_bits),")")
        # print_msg ("PastRateAdjustmentRatio=",PastRateAdjustmentRatio,"EventHorizonDeviationSlow",EventHorizonDeviationSlow,"PastSecondsMin=",PastSecondsMin,"PastSecondsMax=",PastSecondsMax,"PastBlocksMin=",PastBlocksMin,"PastBlocksMax=",PastBlocksMax)

        return new_bits, new_target

    def get_target(self, height, chain=None):
        if bitcoin.TESTNET:
            return 0, 0

        if height == 0:
            return 0x1e0ffff0, 0x00000FFFF0000000000000000000000000000000000000000000000000000000

        return self.KimotoGravityWell(height, chain)

    def connect_header(self, chain, header):
        '''Builds a header chain until it connects.  Returns True if it has
        successfully connected, False if verification failed, otherwise the
        height of the next header needed.'''
        chain.append(header)  # Ordered by decreasing height
        previous_height = header['block_height'] - 1
        previous_header = self.read_header(previous_height)

        # Missing header, request it
        if not previous_header:
            return previous_height

        # Does it connect to my chain?
        prev_hash = self.hash_header(previous_header)
        if prev_hash != header.get('prev_block_hash'):
            self.print_error("reorg")
            return previous_height

        # The chain is complete.  Reverse to order by increasing height
        chain.reverse()
        try:
            self.verify_chain(chain)
            self.print_error("new height:", previous_height + len(chain))
            for header in chain:
                self.save_header(header)
            return True
        except BaseException as e:
            self.print_error(str(e))
            return False

    def connect_chunk(self, idx, hexdata):
        try:
            data = hexdata.decode('hex')
            self.verify_chunk(idx, data)
            self.print_error("validated chunk %d" % idx)
            self.save_chunk(idx, data)
            return idx + 1
        except BaseException as e:
            self.print_error('verify_chunk failed', str(e))
            return idx - 1

    def get_checkpoint(self):
        height = self.config.get('checkpoint_height', 0)
        value = self.config.get('checkpoint_value', bitcoin.GENESIS)
        return (height, value)

    def set_checkpoint(self, height, value):
        self.checkpoint_height = height
        self.checkpoint_hash = value
        self.config.set_key('checkpoint_height', height)
        self.config.set_key('checkpoint_value', value)
        self.check_truncate_headers()
